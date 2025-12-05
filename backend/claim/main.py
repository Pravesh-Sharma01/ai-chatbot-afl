# main.py
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

# FastAPI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Load .env FIRST
from dotenv import load_dotenv
load_dotenv()

# Semantic Kernel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.contents.chat_history import ChatHistory

# Plugins
from plugins.ai_search_plugin import AiSearchPlugin
from plugins.sql_plugin import SqlPlugin
from plugins.neo4j_plugin import Neo4jPlugin

# System Prompt
from prompts import CONVERSATIONAL_AGENT_SYSTEM_PROMPT


# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("claims_planner")

# -------------------------------------------------------------------
# Global Variables
# -------------------------------------------------------------------
kernel: Kernel = None
chat_agent: ChatCompletionAgent = None
chat_history_per_session: dict[str, ChatHistory] = {}

class AskRequest(BaseModel):
    session_id: str
    message: str


# -------------------------------------------------------------------
# Lifespan — Initialise Kernel + Plugins
# -------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global kernel, chat_agent

    logger.info("🔧 Loading environment variables...")
    logger.info(f"AZURE_SQL_SERVER = {os.getenv('AZURE_SQL_SERVER')}")
    logger.info(f"AZURE_SEARCH_ENDPOINT = {os.getenv('AZURE_SEARCH_ENDPOINT')}")
    logger.info(f"NEO4J_URI = {os.getenv('NEO4J_URI')}")

    logger.info("🚀 Initializing Kernel...")
    kernel = Kernel()

    # Load Azure OpenAI
    kernel.add_service(AzureChatCompletion(
        service_id="azure_openai_chat",
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    ))
    logger.info("✅ Azure OpenAI added.")

    # Load Plugins
    kernel.add_plugin(AiSearchPlugin(), plugin_name="AzureSearch")
    kernel.add_plugin(SqlPlugin(), plugin_name="SqlClaims")
    kernel.add_plugin(Neo4jPlugin(), plugin_name="Neo4jClaims")
    logger.info("✅ Plugins registered.")

    chat_agent = ChatCompletionAgent(
        kernel=kernel,
        instructions=CONVERSATIONAL_AGENT_SYSTEM_PROMPT
    )
    logger.info("🤖 Planner Agent ready.")

    yield

    # Shutdown (if needed)
    logger.info("❌ FastAPI application shutdown initiated.")


# -------------------------------------------------------------------
# FastAPI App
# -------------------------------------------------------------------
app = FastAPI(
    title="Claims Planner",
    version="1.0",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# -------------------------------------------------------------------
# /ask endpoint (MAIN ENTRY)
# -------------------------------------------------------------------
@app.post("/ask")
async def ask_planner(req: AskRequest):
    session_id = req.session_id
    user_msg = req.message

    logger.info(f"💬 New query from {session_id}: {user_msg}")

    # Create chat history if new session
    if session_id not in chat_history_per_session:
        chat_history_per_session[session_id] = ChatHistory()
        logger.info(f"New chat session created: {session_id}")
        chat_history_per_session[session_id].add_system_message(CONVERSATIONAL_AGENT_SYSTEM_PROMPT)

    chat_history = chat_history_per_session[session_id]

    if not user_msg and not chat_history.messages:
        pass
    elif not user_msg:
        return {"reply": "Please enter a message."}
    else:
        chat_history.add_user_message(user_msg)

    logger.info(f"Chat History before agent call: {[m.content for m in chat_history.messages]}")

    final_agent_response_content = ""
    try:
        async for agent_response in chat_agent.invoke(chat_history):
            if agent_response.content:
                final_agent_response_content = agent_response.content
            if agent_response.metadata and agent_response.metadata.get('usage'):
                logger.info(f"Agent Token Usage: {agent_response.metadata.get('usage')}")

    except Exception as e:
        logger.error(f"Error during agent invocation: {e}", exc_info=True)
        error_message = "I encountered an issue trying to process your request. Please try rephrasing."
        chat_history.add_assistant_message(error_message)
        return {"reply": error_message}

    response_to_send = str(final_agent_response_content).strip()
    logger.info(f"AI response for session {session_id}: {response_to_send}")

    chat_history.add_assistant_message(response_to_send)
    logger.info(f"Chat History after agent update: {[m.content for m in chat_history.messages]}")

    return {
        "reply": response_to_send
    }


# -------------------------------------------------------------------
# /chat endpoint (for frontend compatibility)
# -------------------------------------------------------------------
@app.post("/chat")
async def chat_endpoint(req: AskRequest):
    """Compatibility endpoint that matches the frontend's expected /chat route"""
    return await ask_planner(req)


# -------------------------------------------------------------------
# Utility Routes
# -------------------------------------------------------------------
@app.get("/")
def home():
    return {"message": "Claims Planner Running ✔", "time": datetime.utcnow().isoformat()}

@app.get("/health")
def health():
    return {"status": "OK", "time": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )