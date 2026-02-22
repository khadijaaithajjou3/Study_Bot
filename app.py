import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pymongo import MongoClient
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()


groq_api_key = os.getenv("GROQ_API_KEY")
mongo_uri= os.getenv("MONGODB_URI")

client = MongoClient(mongo_uri)
db = client["studybot"]
collection = db["chat_history"]

app = FastAPI()

class ChatRequest(BaseModel):
    user_id : str
    question : str

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"],
    allow_credentials =True

)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an AI study assistant. Help users answer academic and educational questions."),
    MessagesPlaceholder(variable_name="history"),
    ("user", "{question}")
])

llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"),model_name ="openai/gpt-oss-20b")
chain = prompt | llm 

user_id = "user31"

def get_history (user_id) :
    chats = collection.find({"user_id" : user_id}).sort("timestamp", 1)
    history = []

    for studybot in chats :
        history.append((studybot["role"], studybot["message"]))
    return history   

@app.get("/") 
def home():
    return{"message" : "Welcome to Study CHATBOT assistant API:"}

@app.post("/studybot")
def studybot(request : ChatRequest):
    history = get_history(request.user_id)
    response = chain.invoke({"history" : history , "question":request.question})

    collection.insert_one({
        "user_id":request.user_id,
        "role": "user",
        "message":request.question,
        "timestamp": datetime.utcnow()
    })

    collection.insert_one({
        "user_id":request.user_id,
        "role": "assistant",
        "message": response.content,
        "timestamp": datetime.utcnow()
    })

    return {"response" : response.content}
    
