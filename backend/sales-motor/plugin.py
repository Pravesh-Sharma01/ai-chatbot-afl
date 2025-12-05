import os
import json
import logging
import time
import tempfile
import shutil
from io import BytesIO

from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document
import faiss

from semantic_kernel.functions.kernel_function_decorator import kernel_function
from azure.storage.fileshare import ShareFileClient, ShareDirectoryClient
from azure.core.exceptions import HttpResponseError

# -----------------------
# Generic Document Plugin
# -----------------------
class GenericDocPlugin:
    """
    Handles documents from Azure File Share, builds FAISS embeddings in batches,
    avoids recomputation for PDFs already embedded, and exposes search tools
    for Semantic Kernel agent.
    """

    def __init__(self):
        self.storage_conn_str = os.environ["AZURE_FILESHARE_CONN_STR"]
        self.share_name = os.environ.get("AZURE_FILESHARE_NAME", "docs_share")
        self.categories = ["client", "competitor"]
        self.root_folder = "ABB"
        self.index_dir = "faiss_index"  # Relative path within file share
        self.metadata_file = "embedded_files.json"  # Relative path within file share

        # Chunk and batching
        self.chunk_size = 4000
        self.chunk_overlap = 200
        self.batch_size = 20
        self.embedding_delay = 0.1  # short delay between batches

        # State
        self.vector_stores = {}
        self._loaded = False
        self.embedded_files = {}

        # Embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=os.environ["AZURE_EMBEDDING_OPENAI_ENDPOINT"],
            azure_deployment=os.environ["AZURE_OPENAI_EMBEDDING_MODEL"],
            api_key=os.environ["AZURE_EMBEDDING_OPENAI_API_KEY"],
        )

        # Ensure index directory exists on the file share
        self._create_directory_on_share(os.path.join(self.root_folder, self.index_dir))
        
        # Load metadata from file share at startup
        metadata_path = os.path.join(self.root_folder, self.metadata_file).replace("\\", "/")
        try:
            metadata_content = self._download_file_from_share(metadata_path)
            self.embedded_files = json.loads(metadata_content.getvalue())
            logging.info("Metadata file loaded from Azure File Share.")
        except HttpResponseError as e:
            if "ResourceNotFound" in str(e):
                logging.warning("Metadata file not found in file share. Starting with empty metadata.")
            else:
                logging.error(f"Failed to load metadata file from file share: {e}")
        except Exception as e:
            logging.error(f"Error reading metadata file: {e}")
    
    # -----------------------
    # Azure File Share Helpers
    # -----------------------
    def _create_directory_on_share(self, directory_path):
        """Creates a directory on the Azure File Share if it doesn't exist."""
        try:
            ShareDirectoryClient.from_connection_string(
                conn_str=self.storage_conn_str,
                share_name=self.share_name,
                directory_path=directory_path
            ).create_directory()
            logging.info(f"Directory '{directory_path}' created on file share.")
        except HttpResponseError as e:
            if e.error_code != "ResourceAlreadyExists":
                raise e

    def _get_directory_client(self, *folders):
        directory_path = "/".join(folders)
        return ShareDirectoryClient.from_connection_string(
            conn_str=self.storage_conn_str,
            share_name=self.share_name,
            directory_path=directory_path
        )

    def _get_file_client(self, directory_client, file_name):
        file_path = os.path.join(directory_client.directory_path, file_name).replace("\\", "/")
        return ShareFileClient.from_connection_string(
            conn_str=self.storage_conn_str,
            share_name=self.share_name,
            file_path=file_path
        )

    def _get_file_text(self, file_client: ShareFileClient):
        try:
            stream = file_client.download_file()
            pdf_bytes = BytesIO()
            stream.readinto(pdf_bytes)
            pdf_bytes.seek(0)
            reader = PdfReader(pdf_bytes)
            return "".join([p.extract_text() or "" for p in reader.pages])
        except Exception as e:
            logging.warning(f"Failed to read PDF: {e}")
            return ""

    def _upload_file_to_share(self, local_path, share_path):
        """Uploads a local file to the Azure File Share."""
        file_client = ShareFileClient.from_connection_string(
            conn_str=self.storage_conn_str,
            share_name=self.share_name,
            file_path=share_path
        )
        
        # Check if file exists and delete it to handle 'overwrite' behavior
        try:
            file_client.get_file_properties()
            file_client.delete_file()
            logging.info(f"Existing file {share_path} deleted.")
        except HttpResponseError as e:
            if e.error_code != "ResourceNotFound":
                raise e

        # Now, upload the file
        with open(local_path, "rb") as source_file:
            file_client.upload_file(source_file)

        logging.info(f"Uploaded {local_path} to {share_path}.")

    def _download_file_from_share(self, share_path):
        """Downloads a file from the Azure File Share to a BytesIO object."""
        file_client = ShareFileClient.from_connection_string(
            conn_str=self.storage_conn_str,
            share_name=self.share_name,
            file_path=share_path
        )
        stream = file_client.download_file()
        content = BytesIO()
        stream.readinto(content)
        content.seek(0)
        return content

    # -----------------------
    # Vector Store Builder
    # -----------------------
    def _build_vector_store(self, category):
        docs = []
        splitter = RecursiveCharacterTextSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        dir_client = self._get_directory_client(self.root_folder, category)
        
        # Paths for FAISS index on the file share
        faiss_share_path = os.path.join(self.root_folder, self.index_dir, f"faiss_{category}")
        self._create_directory_on_share(faiss_share_path)
        faiss_dir_client = self._get_directory_client(self.root_folder, self.index_dir, f"faiss_{category}")
        
        vector_store = None
        
        # Try to download and load FAISS index from the file share
        try:
            faiss_files = [f.name for f in faiss_dir_client.list_directories_and_files()]
            if "index.faiss" in faiss_files and "index.pkl" in faiss_files:
                with tempfile.TemporaryDirectory() as temp_dir:
                    for filename in faiss_files:
                        share_file_path = os.path.join(faiss_share_path, filename).replace("\\", "/")
                        local_file_path = os.path.join(temp_dir, filename)
                        
                        content = self._download_file_from_share(share_file_path)
                        with open(local_file_path, "wb") as f:
                            f.write(content.getvalue())
                            
                    logging.info(f"Loading existing FAISS index for category '{category}' from file share.")
                    vector_store = FAISS.load_local(temp_dir, self.embeddings, allow_dangerous_deserialization=True)
                    
                    if vector_store and vector_store.index.ntotal > 0:
                        logging.info(f"Successfully loaded a valid FAISS index with {vector_store.index.ntotal} vectors.")
                    else:
                        logging.warning("Loaded FAISS index is empty. Will re-index documents.")
                        vector_store = None
            else:
                logging.info(f"No existing valid FAISS index found on file share for category '{category}'.")
        except HttpResponseError as e:
            if "ResourceNotFound" in str(e):
                logging.info(f"FAISS index directory not found. Will create new index for category '{category}'.")
            else:
                logging.error(f"Failed to check FAISS index directory: {e}")
        except Exception as e:
            logging.error(f"Failed to load FAISS index for category '{category}': {e}")
            vector_store = None
        
        all_new_chunks = []
        for item in dir_client.list_directories_and_files():
            if item["is_directory"] or not item["name"].lower().endswith(".pdf"):
                continue

            file_key = f"{category}/{item['name']}"
            if file_key in self.embedded_files:
                logging.info(f"Skipping already embedded PDF: {file_key}")
                continue

            logging.info(f"Processing PDF: {file_key}")
            file_client = self._get_file_client(dir_client, item["name"])
            text = self._get_file_text(file_client)
            if not text:
                continue

            chunks = splitter.split_text(text)
            
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": item["name"],
                        "chunk_id": i,
                        "id": f"{item['name']}::chunk_{i}",
                        "category": category
                    }
                )
                all_new_chunks.append(doc)
            
            # Mark PDF as embedded and save to file share
            self.embedded_files[file_key] = True
            
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp_file:
            json.dump(self.embedded_files, tmp_file, indent=2)
            tmp_file_path = tmp_file.name
        self._upload_file_to_share(tmp_file_path, os.path.join(self.root_folder, self.metadata_file).replace("\\", "/"))
        os.unlink(tmp_file_path)

        # Process and add all new chunks in batches
        if all_new_chunks:
            for i in range(0, len(all_new_chunks), self.batch_size):
                batch_docs = all_new_chunks[i:i + self.batch_size]
                
                embeddings = None
                while True:
                    try:
                        embeddings = self.embeddings.embed_documents([d.page_content for d in batch_docs])
                        break
                    except Exception as e:
                        if "429" in str(e):
                            logging.warning("Rate limit hit. Waiting 60 seconds before retry...")
                            time.sleep(60)
                        else:
                            raise e

                # NEW: Initialize FAISS index here if not already loaded
                if vector_store is None:
                    logging.info("Initializing new FAISS vector store with correct embedding dimension.")
                    embedding_dimension = len(embeddings[0])
                    vector_store = FAISS(
                        embedding_function=self.embeddings,
                        index=faiss.IndexFlatL2(embedding_dimension),
                        docstore=InMemoryDocstore(),
                        index_to_docstore_id={}
                    )

                vector_store.add_texts(
                    [d.page_content for d in batch_docs],
                    metadatas=[d.metadata for d in batch_docs],
                    embeddings=embeddings
                )
                time.sleep(self.embedding_delay)
            
        # Save final FAISS index to the file share
        if vector_store is not None and vector_store.index.ntotal > 0:
            with tempfile.TemporaryDirectory() as temp_dir:
                vector_store.save_local(temp_dir)
                for filename in os.listdir(temp_dir):
                    local_path = os.path.join(temp_dir, filename)
                    share_path = os.path.join(faiss_share_path, filename).replace("\\", "/")
                    self._upload_file_to_share(local_path, share_path)

        if vector_store is None:
            logging.info("No documents to index. Initializing an empty FAISS vector store with default dimension.")
            vector_store = FAISS(
                embedding_function=self.embeddings,
                index=faiss.IndexFlatL2(1536),
                docstore=InMemoryDocstore(),
                index_to_docstore_id={}
            )

        return vector_store

    # -----------------------
    # Load Documents
    # -----------------------
    @kernel_function(name="load_documents", description="Load and index all document categories")
    async def load_documents(self):
        for category in self.categories:
            logging.info(f"Loading category: {category}")
            self.vector_stores[category] = self._build_vector_store(category)
        self._loaded = True
        logging.info("✅ GenericDocPlugin: documents loaded.")

    # -----------------------
    # Search Functions
    # -----------------------
    def _format_results(self, results):
        if not results:
            return "No matching documents found."
        formatted = []
        for doc, score in results:
            formatted.append(
                f"Category: {doc.metadata.get('category')} | "
                f"File: {doc.metadata.get('source')} | "
                f"Score: {score:.2f}\n{doc.page_content[:1000]}"
            )
        return "\n\n".join(formatted)

    @kernel_function(name="search_category", description="Search documents from a specific category")
    async def search_category(self, query: str, category: str, k: int = 5):
        if not self._loaded:
            return "Please call `load_documents` first."
        if category not in self.vector_stores:
            return f"Category '{category}' not found."
        results = self.vector_stores[category].similarity_search_with_score(query, k=k)
        return self._format_results(results)

    @kernel_function(name="search_all", description="Search all categories")
    async def search_all(self, query: str, k: int = 5):
        if not self._loaded:
            return "Please call `load_documents` first."
        results = []
        for vs in self.vector_stores.values():
            results += vs.similarity_search_with_score(query, k=k)
        return self._format_results(results)