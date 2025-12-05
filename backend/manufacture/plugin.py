# plugin.py (optimized)

import json, os
import numpy as np
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import AzureOpenAI
from semantic_kernel.functions import kernel_function

load_dotenv()

# ======================================================
# ENV & CLIENT
# ======================================================
NEO4J_URI       = os.getenv("NEO4J_URI")
NEO4J_USER      = os.getenv("NEO4J_USER")
NEO4J_PASSWORD  = os.getenv("NEO4J_PASSWORD")
DB              = os.getenv("NEO4J_DATABASE", "firstdatabase")

AZURE_EMBED_KEY      = os.getenv("AZURE_EMBEDDING_OPENAI_API_KEY")
AZURE_EMBED_ENDPOINT = os.getenv("AZURE_EMBEDDING_OPENAI_ENDPOINT")
AZURE_EMBED_MODEL    = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

embed_client = AzureOpenAI(
    api_key = AZURE_EMBED_KEY,
    azure_endpoint = AZURE_EMBED_ENDPOINT,
    api_version = "2024-02-15-preview"
)


# ======================================================
# EMBEDDING CACHE
# ======================================================
PRODUCTS = []            # raw product data
VECTORS  = None          # numpy matrix of [app+feature] embeddings


def embed(text: str) -> np.ndarray:
    res = embed_client.embeddings.create(
        model = AZURE_EMBED_MODEL,
        input = text
    )
    return np.array(res.data[0].embedding, dtype=np.float32)


# ======================================================
# LOAD & PRECOMPUTE EMBEDDINGS (RUN ONCE)
# ======================================================
def load_and_cache():
    global PRODUCTS, VECTORS

    cypher = """
    MATCH (p:Product)
    OPTIONAL MATCH (p)-[:HAS_APPLICATION]->(a:Application)
    OPTIONAL MATCH (p)-[:HAS_FEATURE]->(f:Feature)
    RETURN p.name AS name,
           collect(DISTINCT a.text) AS applications,
           collect(DISTINCT f.text) AS features
    """

    with driver.session(database=DB) as session:
        rows = session.run(cypher)
        PRODUCTS = [dict(r) for r in rows]

    # build embeddings ONCE
    vectors = []

    for p in PRODUCTS:
        apps = " ".join(p.get("applications") or [])
        feats = " ".join(p.get("features") or [])
        text = apps + " " + feats

        vectors.append(embed(text))

    VECTORS = np.vstack(vectors)
    print(f"⚡ Cached {len(PRODUCTS)} product embeddings in RAM.")


# ======================================================
# SEMANTIC SEARCH (VERY FAST)
# ======================================================
def search_fast(query: str):

    q_vec = embed(query)

    # cosine similarities vectorized (FAST)
    sims = (VECTORS @ q_vec) / (np.linalg.norm(VECTORS, axis=1)*np.linalg.norm(q_vec))

    idx = np.argmax(sims)   # best match
    best = PRODUCTS[idx]

    return {
        "name": best["name"],
        "applications": best.get("applications", []),
        "features": best.get("features", [])
    }


# ======================================================
# PLUGIN FOR SEMANTIC KERNEL
# ======================================================
class ProductSearchPlugin:

    @kernel_function(description="Fast search for product based on application or feature.")
    def search_products(self, query: str) -> str:

        result = search_fast(query)
        return json.dumps(result, ensure_ascii=False)


# load embeddings ONCE at import
load_and_cache()
