import os
import logging
import uuid
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.contents.chat_history import ChatHistory

from prompt import SYSTEM_PROMPT, AGENT_NAME
from plugin import ProductSearchPlugin, load_and_cache


# -------------------------------------------------------------------
# Load .env
# -------------------------------------------------------------------
load_dotenv()


# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("manufacture_agent")


# -------------------------------------------------------------------
# Globals
# -------------------------------------------------------------------
kernel: Kernel = None
chat_agent: ChatCompletionAgent = None
chat_history_per_session: dict[str, ChatHistory] = {}


class AskRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


# -------------------------------------------------------------------
# FastAPI App
# -------------------------------------------------------------------
app = FastAPI(
    title="ManufactureAgent",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Startup / Shutdown
# -------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    global kernel, chat_agent
    
    logger.info("🚀 Initializing ManufactureAgent ...")

    # Initialize product cache from Neo4j (if available)
    try:
        load_and_cache()
    except Exception as e:
        logger.warning(f"⚠️ Could not initialize product cache: {e}")
        logger.info("Continuing without product cache...")

    logger.info("Initializing Semantic Kernel client...")
    
    kernel = Kernel()
    kernel.add_service(
        AzureChatCompletion(
            service_id="azure_openai_chat",
            deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
        ),
    )
    logger.info("✅ Azure AI service added.")

    # Add the local plugin
    kernel.add_plugin(ProductSearchPlugin(), plugin_name="ProductSearchToolbox")
    logger.info("✅ Local ProductSearchToolbox plugin registered.")

    chat_agent = ChatCompletionAgent(
        kernel=kernel,
        instructions=SYSTEM_PROMPT
    )
    logger.info("✅ Semantic Kernel ChatCompletionAgent initialized.")
    logger.info("🤖 ManufactureAgent ready.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("❌ FastAPI shutdown.")


# -------------------------------------------------------------------
# POST /ask  (main endpoint)
# -------------------------------------------------------------------
@app.post("/ask")
async def ask_agent(req: AskRequest):
    # Generate session_id if not provided
    session_id = req.session_id
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(f"Generated new session_id: {session_id}")

    user_msg = req.message

    logger.info(f"💬 New query from {session_id}: {user_msg}")

    # Create chat history if new session
    if session_id not in chat_history_per_session:
        chat_history_per_session[session_id] = ChatHistory()
        logger.info(f"New chat session created: {session_id}")
        chat_history_per_session[session_id].add_system_message(SYSTEM_PROMPT)

    chat_history = chat_history_per_session[session_id]

    if not user_msg and not chat_history.messages:
        pass
    elif not user_msg:
        return {"reply": "Please enter a message.", "session_id": session_id}
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
        return {"reply": error_message, "session_id": session_id}
    
    response_to_send = str(final_agent_response_content).strip()
    logger.info(f"AI response for session {session_id}: {response_to_send}")

    chat_history.add_assistant_message(response_to_send)
    logger.info(f"Chat History after agent update: {[m.content for m in chat_history.messages]}")

    return {
        "reply": response_to_send,
        "session_id": session_id
    }


# -------------------------------------------------------------------
# POST /chat  (frontend compatibility)
# -------------------------------------------------------------------
@app.post("/chat")
async def chat(req: AskRequest):
    return await ask_agent(req)


# -------------------------------------------------------------------
# Utility
# -------------------------------------------------------------------
@app.get("/")
def home():
    return {
        "message": "ManufactureAgent Running ✔",
        "time": datetime.utcnow().isoformat()
    }


@app.get("/health")
def health():
    return {"status": "OK"}


# -------------------------------------------------------------------
# Run server
# -------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8005"))
    print(f"🚀 Starting Manufacture Agent on http://127.0.0.1:{port}")
    print(f"📚 API docs available at http://127.0.0.1:{port}/docs")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=port,
        reload=True,
        log_level="info"
    )





