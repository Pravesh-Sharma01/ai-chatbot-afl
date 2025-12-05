# plugins/sql_plugin.py
import os, json, logging

# Handle optional semantic_kernel import for testing
try:
    from semantic_kernel.functions.kernel_function_decorator import kernel_function
except ImportError:
    def kernel_function(name=None, description=None):
        def decorator(func):
            return func
        return decorator

try:
    import pyodbc
except ImportError:
    pyodbc = None

logger = logging.getLogger("sql_plugin")


class SqlPlugin:

    def __init__(self):
        # --- Read SQL config from .env ---
        server = os.getenv("AZURE_SQL_SERVER")
        database = os.getenv("AZURE_SQL_DATABASE")
        user = os.getenv("AZURE_SQL_USER")
        password = os.getenv("AZURE_SQL_PASSWORD")
        driver = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 18 for SQL Server")

        # --- Build proper connection string ---
        self.conn_str = (
            f"Driver={{{driver}}};"
            f"Server=tcp:{server},1433;"
            f"Database={database};"
            f"Uid={user};"
            f"Pwd={password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )

        print("\n🔌 SQL CONNECTION STRING FOR DEBUG:")
        print(self.conn_str)


    @kernel_function(name="get_claim_from_sql",
                     description="Get claim data from SQL database by claimId (e.g., CLM001)")
    async def get_claim_from_sql(self, query: str) -> str:

        if pyodbc is None:
            return json.dumps({"error": "pyodbc_not_installed"})

        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()

        
            cursor.execute(query)

            row = cursor.fetchone()
            columns = [column[0] for column in cursor.description]

            if not row:
                return json.dumps({"result": None})

            # --- FIXED SERIALIZATION HANDLING ---
            result = {}
            for col, val in zip(columns, row):

                # Convert DATE / DATETIME
                if hasattr(val, "isoformat"):
                    result[col] = val.isoformat()

                # Convert DECIMAL → float
                elif str(type(val)).endswith("Decimal'>"):
                    result[col] = float(val)

                else:
                    result[col] = val

            conn.close()
            return json.dumps(result)

        except Exception as e:
            logger.exception("get_claim_from_sql failed")
            return json.dumps({"error": str(e)})
