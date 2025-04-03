from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from wingman.core.wingmanOA import WingmanOpenAI
import os
from dotenv import load_dotenv
import datetime

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)


assistant = WingmanOpenAI(model_name="llama-3.3-70b-versatile", api_key=os.getenv("API_KEY"))

class InputPayload(BaseModel):
    message: str



@app.post("/chat")
async def chat(payload: InputPayload):
    thread_id = datetime.datetime.now().strftime('%d%m%Y')
    response = assistant.run(payload.message, thread_id)
    return {"response": response}


@app.get("/conversations")
def get_conversation(date: str = Query(..., alias="date")):
    """
    Get the full conversation for a given thread_id (mapped from `date` query param).
    """
    try:
        yyyy, mm, dd = date.split("-")
        thread_id = f"{dd}{mm}{yyyy}"
        history = assistant.memory.get_thread_history(thread_id)
        return { "conversations": history if history else [] }
    except Exception as e:
        print("Error fetching conversation:", e)
        return { "conversations": [] }


@app.delete("/conversations")
def delete_conversation(date: str = Query(..., alias="date")):
    try:
        yyyy, mm, dd = date.split("-")
        thread_id = f"{dd}{mm}{yyyy}"
        assistant.memory.delete_thread_history(thread_id)
        return { "success": True }
    except Exception as e:
        print("Error deleting conversation:", e)
        return { "success": False }