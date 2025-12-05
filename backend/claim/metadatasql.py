# plugins/sql_metadata_plugin.py
import os, json, logging

from dotenv import load_dotenv
load_dotenv()


# Handle Semantic Kernel decorator
try:
    from semantic_kernel.functions.kernel_function_decorator import kernel_function
except ImportError:
    def kernel_function(name=None, description=None):
        def decorator(func):
            return func
        return decorator

# ODBC
try:
    import pyodbc
except ImportError:
    pyodbc = None


logger = logging.getLogger("sql_metadata_plugin")


class SqlMetadataPlugin:

    def __init__(self):
        # Load config from .env
        server = os.getenv("AZURE_SQL_SERVER")
        database = os.getenv("AZURE_SQL_DATABASE")
        user = os.getenv("AZURE_SQL_USER")
        password = os.getenv("AZURE_SQL_PASSWORD")
        driver = os.getenv("AZURE_SQL_DRIVER", "ODBC Driver 18 for SQL Server")

        # Build connection string
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

        print("\n🔍 SQL METADATA CONNECTION STRING:")
        print(self.conn_str)


    # ----------------------------------------------------------------------
    # 1) GET ALL TABLES FROM DBO
    # ----------------------------------------------------------------------
    @kernel_function(
        name="list_tables",
        description="Return list of all tables inside dbo schema"
    )
    async def list_tables(self) -> str:

        if pyodbc is None:
            return json.dumps({"error": "pyodbc_not_installed"})

        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()

            query = """
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo'
            ORDER BY TABLE_NAME
            """

            cursor.execute(query)
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            return json.dumps({"tables": tables})

        except Exception as e:
            logger.exception("list_tables failed")
            return json.dumps({"error": str(e)})


    # ----------------------------------------------------------------------
    # 2) GET COLUMN METADATA FOR A SPECIFIC TABLE
    # ----------------------------------------------------------------------
    @kernel_function(
        name="get_table_metadata",
        description="Return columns + datatypes of a specific table"
    )
    async def get_table_metadata(self, table_name: str) -> str:

        if pyodbc is None:
            return json.dumps({"error": "pyodbc_not_installed"})

        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()

            query = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
            """

            cursor.execute(query, table_name)
            rows = cursor.fetchall()

            metadata = []
            for row in rows:
                metadata.append({
                    "column": row.COLUMN_NAME,
                    "datatype": row.DATA_TYPE,
                    "nullable": row.IS_NULLABLE
                })

            conn.close()
            print({
                "table": table_name,
                "columns": metadata
            })

            return json.dumps({
                "table": table_name,
                "columns": metadata
            })

        except Exception as e:
            logger.exception("get_table_metadata failed")
        
            return json.dumps({"error": str(e)})


    # ----------------------------------------------------------------------
    # 3) FULL DATABASE METADATA (ALL TABLES + COLUMNS)
    # ----------------------------------------------------------------------
    @kernel_function(
        name="get_full_metadata",
        description="Return metadata for all dbo tables"
    )
    async def get_full_metadata(self) -> str:

        if pyodbc is None:
            return json.dumps({"error": "pyodbc_not_installed"})

        try:
            conn = pyodbc.connect(self.conn_str)
            cursor = conn.cursor()

            # STEP 1 – Get tables
            cursor.execute("""
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo'
            """)
            tables = [row[0] for row in cursor.fetchall()]

            full_meta = {}

            # STEP 2 – For each table, get columns
            for tbl in tables:
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                """, tbl)

                rows = cursor.fetchall()
                full_meta[tbl] = [
                    {
                        "column": row.COLUMN_NAME,
                        "datatype": row.DATA_TYPE,
                        "nullable": row.IS_NULLABLE
                    }
                    for row in rows
                ]
            print(full_meta)
            conn.close()

            return json.dumps(full_meta)

        except Exception as e:
            logger.exception("get_full_metadata failed")
            return json.dumps({"error": str(e)})
        

if __name__ == "__main__":
    import asyncio

    asyncio.run( SqlMetadataPlugin().get_full_metadata() )
 
