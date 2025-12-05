# plugins/ai_search_plugin.py
import os, json, logging
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger("ai_search_plugin")

class AiSearchPlugin:
    def __init__(self):
        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        key = os.getenv("AZURE_SEARCH_KEY")
        index = os.getenv("AZURE_SEARCH_INDEX_NAME", "insurance")
        if not endpoint or not key:
            logger.warning("Azure Search not configured (AZURE_SEARCH_ENDPOINT/KEY missing)")
            self.client = None
        else:
            self.client = SearchClient(endpoint=endpoint, index_name=index, credential=AzureKeyCredential(key))

    @kernel_function(name="search_claim_documents", description="Search documents related to a claim id or free text.")
    async def search_claim_documents(self, query: str) -> str:
        """
        query: either a claim id (CLM001) or free text
        Return: JSON string list of {id, file_name, @search.score}
        """
        try:
            if not self.client:
                return json.dumps({"error": "azure_search_not_configured"})

            # If query looks like a claim id, search for that id in any fields
            results = []
            if query.upper().startswith("CLM"):
                # search for document containing CLMxxx in content or metadata
                resp = self.client.search(search_text=query, top=10)
            else:
                resp = self.client.search(search_text=query, top=10)

            for r in resp:
                # each r is a SearchDocument (dict-like). Keep only a few fields
                results.append({
                    "id": r.get("id"),
                    "file_name": r.get("file_name"),
                    "score": float(r.get("@search.score", 0)),
                    "content": r.get("content")

                })
            return json.dumps(results)
        except Exception as e:
            logger.exception("search_claim_documents failed")
            return json.dumps({"error": str(e)})

    @kernel_function(name="list_claim_pdfs", description="List pdf documents in search index")
    async def list_claim_pdfs(self) -> str:
        if not self.client:
            return json.dumps({"error":"azure_search_not_configured"})
        try:
            resp = self.client.search(search_text="*", top=50)
            out = [{"id":r.get("id"), "file_name": r.get("file_name")} for r in resp]
            return json.dumps(out)
        except Exception as e:
            logger.exception("list_claim_pdfs failed")
            return json.dumps({"error": str(e)})
