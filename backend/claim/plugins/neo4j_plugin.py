import os, json, logging
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from neo4j import GraphDatabase

logger = logging.getLogger("neo4j_plugin")

class Neo4jPlugin:
    def __init__(self):
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        pwd = os.getenv("NEO4J_PASS")  # IMPORTANT: env uses NEO4J_PASS

        self.driver = None
        if uri and user and pwd:
            try:
                self.driver = GraphDatabase.driver(uri, auth=(user, pwd))
                logger.info("Neo4j driver initialized successfully")
            except Exception as e:
                logger.exception("Neo4j driver init failed")

    # -------------------------------
    # ⭐ TEST CONNECTION (IMPORTANT)
    # -------------------------------
    @kernel_function(name="test_connection", description="Test Neo4j connectivity")
    async def test_connection(self) -> str:
        if not self.driver:
            return json.dumps({"error": "neo4j_not_connected"})

        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS ok").single()
                return json.dumps({"status": "connected", "result": result['ok']})
        except Exception as e:
            logger.exception("Neo4j test_connection failed")
            return json.dumps({"error": str(e)})

    # -------------------------------
    # ⭐ GET CLAIM GRAPH
    # -------------------------------
    @kernel_function(name="get_claim_graph", description="Get claim node and neighbors")
    async def get_claim_graph(self, claim_id: str) -> str:
        if not self.driver:
            return json.dumps({"error": "neo4j_not_connected"})

        try:
            with self.driver.session() as session:
                cypher = """
                MATCH (c:Claim {claimId:$claimId})
                OPTIONAL MATCH (c)-[r]-(n)
                RETURN c, collect({rel: type(r), props: properties(r), node: properties(n), labels: labels(n)}) AS neighbors
                """
                rec = session.run(cypher, claimId=claim_id).single()

                if not rec:
                    return json.dumps({"result": None})

                return json.dumps({
                    "claim": dict(rec["c"]),
                    "neighbors": rec["neighbors"]
                })
        except Exception as e:
            logger.exception("get_claim_graph failed")
            return json.dumps({"error": str(e)})

    # -------------------------------
    # ⭐ ADMIN: NOT USED NOW
    # -------------------------------
    @kernel_function(name="auto_link_docs", description="Admin: Stub only")
    async def auto_link_docs(self) -> str:
        return json.dumps({"info": "auto_link_docs not implemented"})
