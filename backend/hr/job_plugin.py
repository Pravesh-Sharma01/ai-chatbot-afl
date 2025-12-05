import logging
import os
import json
import uuid
from datetime import datetime
from typing import List, Optional
from azure.cosmos import CosmosClient
from azure.storage.fileshare import ShareClient
import pdfplumber
from io import BytesIO
from semantic_kernel.functions.kernel_function_decorator import kernel_function

# ------------------ Logging ------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("job_plugin")

# ------------------ Azure Configuration ------------------
COSMOS_DB_ENDPOINT = os.getenv("COSMOS_DB_ENDPOINT")
COSMOS_DB_KEY = os.getenv("COSMOS_DB_KEY")
COSMOS_DB_DATABASE_ID = os.getenv("COSMOS_DB_DATABASE_ID")
COSMOS_DB_CONTAINER_ID = os.getenv("COSMOS_DB_CONTAINER_ID")

AZURE_FILESHARE_CONN_STR = os.getenv("AZURE_FILESHARE_CONN_STR")
AZURE_FILESHARE_NAME = os.getenv("AZURE_FILESHARE_NAME")

# Initialize Azure clients
try:
    cosmos_client = CosmosClient(COSMOS_DB_ENDPOINT, COSMOS_DB_KEY)
    database = cosmos_client.get_database_client(COSMOS_DB_DATABASE_ID)
    container = database.get_container_client(COSMOS_DB_CONTAINER_ID)
    logger.info("Successfully initialized Cosmos DB client.")
except Exception as e:
    logger.error(f"Failed to initialize Cosmos DB client: {e}")
    cosmos_client = None
    container = None

try:
    share_client = ShareClient.from_connection_string(AZURE_FILESHARE_CONN_STR, AZURE_FILESHARE_NAME)
    logger.info("Successfully initialized Azure Fileshare client.")
except Exception as e:
    logger.error(f"Failed to initialize Azure Fileshare client: {e}")
    share_client = None

class JobSearchPlugin:
    """
    A plugin for handling job search and application processes.
    """

    @kernel_function(
        name="get_latest_jobs",
        description="Returns the 10 most recent job openings in JSON format."
    )
    def get_latest_jobs(self) -> str:
        """
        Returns the 10 most recent job openings.
        """
        if not container:
            return json.dumps({"jobs_found": False, "message": "Cosmos DB client is not initialized."})
        try:
            latest_jobs_query = (
                "SELECT TOP 10 c.id, c.job_title, c.location, c.min_experience FROM c ORDER BY c._ts DESC"
            )
            jobs = list(container.query_items(query=latest_jobs_query, enable_cross_partition_query=True))

            if not jobs:
                return json.dumps({"jobs_found": False, "message": "No job openings available at this time."})

            return json.dumps({"jobs_found": True, "jobs": jobs})

        except Exception as e:
            logger.error(f"Error fetching latest jobs: {e}")
            return json.dumps({"jobs_found": False, "message": "Error occurred while retrieving latest jobs."})

    
    @kernel_function(
        name="search_jobs_by_title_and_experience",
        description="Searches for jobs by title and experience.",
    )
    def search_jobs_by_title_and_experience(self, title: str, experience: int) -> str:
        if not container:
            return json.dumps({"jobs_found": False, "message": "Cosmos DB client is not initialized."})
        try:
            query = (
                f"SELECT TOP 10 c.id, c.job_title, c.location, c.min_experience "
                f"FROM c WHERE CONTAINS(c.job_title_lower, '{title.lower()}') "
                #f"AND c.min_experience <= {experience}"
            )
            jobs = list(container.query_items(query=query, enable_cross_partition_query=True))

            return json.dumps({"jobs_found": True, "jobs": jobs})
        except Exception as e:
            logger.error(f"Error performing job search: {e}")
            return json.dumps({"jobs_found": False, "message": "An error occurred during job search."})

    @kernel_function(
        name="get_job_description",
        description="Retrieves the full job description for a given job ID.",
    )
    def get_job_description(self, job_id: str) -> str:
        if not share_client:
            return json.dumps({"error": "Azure Fileshare client is not initialized."})
        try:
            file_client = share_client.get_file_client(f"{job_id}.txt")
            if file_client.exists():
                downloaded_file = file_client.download_file()
                return downloaded_file.readall().decode("utf-8")
            
            file_client = share_client.get_file_client(f"{job_id}.pdf")
            if file_client.exists():
                downloaded_file = file_client.download_file()
                with pdfplumber.open(BytesIO(downloaded_file.readall())) as pdf:
                    text = "".join(page.extract_text() for page in pdf.pages)
                    return text

            return json.dumps({"error": f"No job description file found for ID {job_id}."})
        except Exception as e:
            logger.error(f"Error retrieving job description for job_id {job_id}: {e}")
            return json.dumps({"error": f"Could not retrieve the job description for ID {job_id}."})

    @kernel_function(
        name="save_applicant_data",
        description="Saves the applicant's data, including personal details and screening questions and answers, to the same container with category 'applicants'.",
    )
    def save_applicant_data(self, full_name: str, email: str, phone_number: str, screening_questions: dict) -> str:
        if not container:
            return json.dumps({"success": False, "message": "Cosmos DB client is not initialized."})
        try:
            applicant_item = {
                "id": str(uuid.uuid4()),
                "category": "applicants",
                "full_name": full_name,
                "email": email,
                "phone_number": phone_number,
                "screening_questions": screening_questions,
                "application_date": datetime.now().isoformat()
            }
            container.create_item(body=applicant_item)
            logger.info(f"Successfully saved applicant data for {full_name}.")
            return json.dumps({"success": True, "message": "Applicant data saved successfully."})
        except Exception as e:
            logger.error(f"Error saving applicant data: {e}")
            return json.dumps({"success": False, "message": f"Error saving applicant data: {e}"})