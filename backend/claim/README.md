# Claims Planner Backend

## Local Development Setup

### 1. Install Dependencies

```bash
cd backend/claim
pip install -r requirements.txt
```

### 2. Create .env File

Create a `.env` file in the `backend/claim` directory with the following variables:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=your-azure-openai-endpoint
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Azure SQL Database Configuration
AZURE_SQL_SERVER=your-sql-server.database.windows.net
AZURE_SQL_DATABASE=your-database-name
AZURE_SQL_USER=your-sql-username
AZURE_SQL_PASSWORD=your-sql-password
AZURE_SQL_DRIVER=ODBC Driver 18 for SQL Server

# Azure Search Configuration
AZURE_SEARCH_ENDPOINT=your-search-endpoint
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX_NAME=insurance

# Neo4j Configuration
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=your-neo4j-username
NEO4J_PASS=your-neo4j-password

# Server Port (optional, defaults to 8000)
PORT=8000
```

### 3. Run Locally

**Option 1: Using the run script**
```bash
python run_local.py
```

**Option 2: Using main.py directly**
```bash
python main.py
```

**Option 3: Using uvicorn directly**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

### 4. Test the API

- Health check: `http://localhost:8000/health`
- Chat endpoint: `POST http://localhost:8000/chat`
- Ask endpoint: `POST http://localhost:8000/ask`

Example request:
```json
{
  "session_id": "test-123",
  "message": "How many total claims exist?"
}
```

### 5. API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker Development

After testing locally, you can test with Docker:

```bash
docker-compose up claim
```

