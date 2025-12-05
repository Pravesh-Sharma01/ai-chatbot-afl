#-------FastAPI Version of the above CLI agent----------


import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from semantic_kernel.agents.chat_completion.chat_completion_agent import (
    ChatCompletionAgent,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)

from prompt import SYSTEM_PROMPT, AGENT_NAME
from plugin import ProductSearchPlugin


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
logger = logging.getLogger("fiber_agent")


# -------------------------------------------------------------------
# Globals
# -------------------------------------------------------------------
agent: ChatCompletionAgent = None
threads: dict[str, object] = {}   # session_id -> thread


class AskRequest(BaseModel):
    session_id: str
    message: str


# -------------------------------------------------------------------
# Lifespan (startup / shutdown)
# -------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):

    global agent

    logger.info("🚀 Initializing FiberGraphAgent ...")

    chat_service = AzureChatCompletion(
        service_id="azure-openai",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
    )

    product_plugin = ProductSearchPlugin()

    agent = ChatCompletionAgent(
        service=chat_service,
        name=AGENT_NAME,
        instructions=SYSTEM_PROMPT,
        plugins=[product_plugin],
    )

    logger.info("🤖 FiberGraphAgent ready.")
    yield

    logger.info("❌ FastAPI shutdown.")


# -------------------------------------------------------------------
# FastAPI App
# -------------------------------------------------------------------
app = FastAPI(
    title="FiberGraphAgent",
    version="1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# POST /ask  (main endpoint)
# -------------------------------------------------------------------
@app.post("/ask")
async def ask_agent(req: AskRequest):

    session_id = req.session_id
    user_msg = req.message

    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Restore thread, or create a new one
    thread = threads.get(session_id)

    try:
        response = await agent.get_response(
            messages=user_msg,
            thread=thread
        )

        # Save updated thread
        threads[session_id] = response.thread

        return {
            "reply": str(response).strip()
        }

    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
        return {
            "reply": "⚠️ Something went wrong while processing request."
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
        "message": "FiberGraphAgent Running ✔",
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
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )





