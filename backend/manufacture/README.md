# Manufacture Agent Backend

A FastAPI-based conversational AI agent for product search and manufacturing guidance. This backend uses Semantic Kernel with Azure OpenAI and Neo4j to provide intelligent product recommendations based on application needs and features.

## Features

- **Conversational Agent**: Maintains conversation history across multiple messages using ChatHistory
- **Product Search**: Semantic search for products using Neo4j graph database
- **Embedding-based Matching**: Uses Azure OpenAI embeddings for fast and accurate product matching
- **Session Management**: Automatic session ID generation and conversation state management
- **Neo4j Integration**: Connects to Neo4j to query product data with applications and features

## Local Development Setup

### 1. Install Dependencies

```bash
cd backend/manufacture
pip install -r requirements.txt
```

### 2. Create .env File

Create a `.env` file in the `backend/manufacture` directory with the following variables:

```env
# Azure OpenAI Configuration (for chat)
AZURE_OPENAI_ENDPOINT=your-azure-openai-endpoint
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure OpenAI Configuration (for embeddings)
AZURE_EMBEDDING_OPENAI_ENDPOINT=your-embedding-endpoint
AZURE_EMBEDDING_OPENAI_API_KEY=your-embedding-api-key
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-large_RAG2

# Neo4j Configuration
NEO4J_URI=neo4j+s://your-neo4j-host:7687
NEO4J_USER=your-neo4j-username
NEO4J_PASSWORD=your-neo4j-password
NEO4J_DATABASE=firstdatabase

# Server Port (optional, defaults to 8005)
PORT=8005
```

### 3. Run Locally

**Option 1: Using main.py directly (Recommended)**
```bash
python main.py
```

**Option 2: Using uvicorn directly**
```bash
uvicorn main:app --host 127.0.0.1 --port 8005 --reload
```

The server will start on `http://127.0.0.1:8005`

### 4. Test the API

- Health check: `http://127.0.0.1:8005/health`
- Chat endpoint: `POST http://127.0.0.1:8005/chat`
- Ask endpoint: `POST http://127.0.0.1:8005/ask`

Example request:
```json
{
  "session_id": "test-123",
  "message": "I need a product for high temperature applications"
}
```

Example response:
```json
{
  "reply": "{\"name\": \"ProductName\", \"applications\": [\"High Temperature\"], \"features\": [\"Heat Resistant\"]}",
  "session_id": "test-123"
}
```

**Note**: If `session_id` is not provided, a new UUID will be automatically generated.

### 5. API Documentation

Once running, visit:
- Swagger UI: `http://127.0.0.1:8005/docs`
- ReDoc: `http://127.0.0.1:8005/redoc`

## Architecture

### Components

1. **FastAPI Application**: REST API server with CORS support
2. **Semantic Kernel**: AI orchestration framework
3. **ChatCompletionAgent**: Conversational AI agent with memory
4. **ProductSearchPlugin**: Plugin for semantic product search
5. **Neo4j Integration**: Graph database for product data
6. **Azure OpenAI**: For both chat completions and embeddings

### How It Works

1. **Startup**: 
   - Loads product data from Neo4j
   - Generates embeddings for all products (applications + features)
   - Caches embeddings in memory for fast search

2. **Request Handling**:
   - Creates or retrieves chat history for the session
   - Adds user message to chat history
   - Invokes the conversational agent with chat history
   - Agent uses ProductSearchPlugin to find matching products
   - Returns product information in JSON format

3. **Product Search**:
   - Uses semantic similarity (cosine similarity) on embeddings
   - Matches user query against cached product embeddings
   - Returns the best matching product with applications and features

## Docker Development

After testing locally, you can test with Docker:

```bash
docker-compose up manufacture
```

The service will be available at `http://127.0.0.1:8005`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Yes |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | Yes |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Chat model deployment name | Yes |
| `AZURE_OPENAI_API_VERSION` | API version | Yes |
| `AZURE_EMBEDDING_OPENAI_ENDPOINT` | Embedding endpoint URL | Yes |
| `AZURE_EMBEDDING_OPENAI_API_KEY` | Embedding API key | Yes |
| `AZURE_OPENAI_EMBEDDING_MODEL` | Embedding model name | Yes |
| `NEO4J_URI` | Neo4j connection URI | Yes |
| `NEO4J_USER` | Neo4j username | Yes |
| `NEO4J_PASSWORD` | Neo4j password | Yes |
| `NEO4J_DATABASE` | Neo4j database name | No (defaults to "firstdatabase") |
| `PORT` | Server port | No (defaults to 8005) |

## API Endpoints

### POST /chat
Main endpoint for chat interactions. Accepts messages and maintains conversation history.

**Request Body:**
```json
{
  "session_id": "optional-session-id",
  "message": "user message"
}
```

**Response:**
```json
{
  "reply": "agent response",
  "session_id": "session-id"
}
```

### POST /ask
Alias for `/chat` endpoint for compatibility.

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "OK"
}
```

### GET /
Root endpoint with service information.

**Response:**
```json
{
  "message": "ManufactureAgent Running ✔",
  "time": "2024-12-05T17:30:40.123456"
}
```

## Error Handling

- If Neo4j is not available, the service will start but product search will return empty results
- If session_id is not provided, a new UUID is automatically generated
- Errors during agent invocation are caught and return user-friendly error messages
- All errors are logged for debugging

## Notes

- Product embeddings are loaded once at startup for performance
- If Neo4j connection fails at startup, the service continues without product cache
- Conversation history is maintained in memory (not persisted)
- Each session maintains its own chat history

## Troubleshooting

### Neo4j Connection Issues
If you see warnings about Neo4j connection:
- Verify your Neo4j credentials in `.env`
- Ensure Neo4j is running and accessible
- Check network connectivity to Neo4j instance
- The service will continue to work but product search will be unavailable

### Port Already in Use
If port 8005 is already in use:
- Change the `PORT` environment variable
- Or stop the process using port 8005
- Update frontend configuration to match the new port

### Embedding Model Issues
If embeddings fail to generate:
- Verify `AZURE_EMBEDDING_OPENAI_API_KEY` and endpoint
- Check that the embedding model name is correct
- Ensure you have quota/access to the embedding model

