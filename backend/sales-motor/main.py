# main.py
import asyncio
import logging
import os
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.contents.chat_history import ChatHistory
from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi import Query
from plugin import GenericDocPlugin
from prompts import SYSTEM_PROMPT

# -----------------------
# Environment
# -----------------------
load_dotenv()
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")
if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_DEPLOYMENT_NAME]):
    raise ValueError(
        "Please ensure AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and "
        "AZURE_DEPLOYMENT_NAME environment variables are set."
    )

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sse_api_backend")

app = FastAPI(title="Sales motor API with Semantic Kernel")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Semantic Kernel Setup ---
kernel: Kernel
chat_agent: ChatCompletionAgent
chat_history_per_session: dict[str, ChatHistory] = {}
doc_plugin: GenericDocPlugin



class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.on_event("startup")
async def startup_event():
    global kernel, chat_agent
    logger.info("Initializing Semantic Kernel client...")

    kernel = Kernel()
    kernel.add_service(
        AzureChatCompletion(
            service_id="azure_openai_chat",
            deployment_name=AZURE_DEPLOYMENT_NAME,
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_API_VERSION,
        ),
    )
    logger.info("✅ Azure AI service added.")

    doc_plugin = GenericDocPlugin()
    await doc_plugin.load_documents()
    kernel.add_plugin(doc_plugin)
    logger.info("✅ Document plugin loaded.")


    chat_agent = ChatCompletionAgent(
        kernel=kernel,
        instructions=SYSTEM_PROMPT
    )
    logger.info("✅ Semantic Kernel ChatCompletionAgent initialized.")

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    logger.info(f"Received chat request from session_id: {request.session_id}, message: {request.message}")

    if request.session_id not in chat_history_per_session:
        chat_history_per_session[request.session_id] = ChatHistory()
        logger.info(f"New chat session created: {request.session_id}")
        chat_history_per_session[request.session_id].add_system_message(SYSTEM_PROMPT)

    chat_history = chat_history_per_session[request.session_id]

    if not request.message and not chat_history.messages:
        pass
    elif not request.message:
        return {"reply": "Please enter a message."}
    else:
        chat_history.add_user_message(request.message)

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
    logger.info(f"AI response for session {request.session_id}: {response_to_send}")

    chat_history.add_assistant_message(response_to_send)
    logger.info(f"Chat History after agent update: {[m.content for m in chat_history.messages]}")

    return {"reply": response_to_send}


@app.get("/")
async def root():
    return {"message": "Welcome to the Job Application API!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("❌ FastAPI client application shutdown initiated.")

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[dict]  # Each message has 'role' and 'content'

@app.get("/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(session_id: str = Query(..., description="Session ID to fetch chat history")):
    """
    Returns the chat history for a given session_id.
    """
    if session_id not in chat_history_per_session:
        return {"session_id": session_id, "messages": []}

    chat_history = chat_history_per_session[session_id]
    history_messages = []

    for message in chat_history.messages:
        if message.role == "system":
            continue  # Skip system messages
        history_messages.append({
            "role": message.role.value if hasattr(message.role, "value") else str(message.role),
            "content": message.content
        })


    return {"session_id": session_id, "messages": history_messages}
 