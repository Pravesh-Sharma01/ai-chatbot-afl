# product_plugin.py

import logging
import os
import json
from datetime import datetime
from typing import List
from azure.cosmos import CosmosClient
from semantic_kernel.functions.kernel_function_decorator import kernel_function

# ------------------ Logging ------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("product_plugin")

# ------------------ Azure Configuration ------------------
COSMOS_DB_ENDPOINT = os.getenv("COSMOS_DB_ENDPOINT")
COSMOS_DB_KEY = os.getenv("COSMOS_DB_KEY")
COSMOS_DB_DATABASE_ID = os.getenv("COSMOS_DB_DATABASE_ID")
COSMOS_DB_CONTAINER_ID = os.getenv("COSMOS_DB_CONTAINER_ID")

if not all([COSMOS_DB_ENDPOINT, COSMOS_DB_KEY, COSMOS_DB_DATABASE_ID, COSMOS_DB_CONTAINER_ID]):
    logger.warning("Cosmos DB environment variables are not set. Product tools will not work.")
    cosmos_client = None
    container = None
else:
    try:
        cosmos_client = CosmosClient(COSMOS_DB_ENDPOINT, COSMOS_DB_KEY)
        database = cosmos_client.get_database_client(COSMOS_DB_DATABASE_ID)
        container = database.get_container_client(COSMOS_DB_CONTAINER_ID)
        logger.info("Successfully initialized Cosmos DB client.")
    except Exception as e:
        logger.error(f"Failed to initialize Cosmos DB client: {e}")
        cosmos_client = None
        container = None

class ProductPlugin:
    """
    A plugin for retrieving product data from a Cosmos DB.
    """

    @kernel_function(
        name="get_all_products",
        description="Returns all products from the Cosmos DB container."
    )
    def get_all_products(self) -> str:
        """
        Returns all products from the Cosmos DB container.
        """
        if not container:
            return json.dumps({"products_found": False, "message": "Cosmos DB client is not initialized."})
        try:
            # Assuming products are marked with category 'products'
            query = "SELECT * FROM c WHERE c.category = 'products'"
            products = list(container.query_items(query=query, enable_cross_partition_query=True))
            return json.dumps({"products_found": True, "products": products})
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return json.dumps({"products_found": False, "message": f"Error fetching products: {e}"})

    @kernel_function(
        name="get_current_datetime",
        description="Gets the current datetime in ISO format."
    )
    def get_current_datetime(self) -> str:
        """
        Gets the current datetime in ISO format.
        """
        return datetime.now().isoformat()