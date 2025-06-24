from pymongo import MongoClient
import os
import pandas as pd
import numpy as np
from io import StringIO

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["allytics"]
users_collection = db["users"]

def register_user(username, password, name):
    if users_collection.find_one({"username": username}):
        return False
    users_collection.insert_one({
        "username": username,
        "password": password,
        "name": name,
        "file_sessions": {}
    })
    return True

def authenticate_user(username, password):
    return users_collection.find_one({"username": username, "password": password})

def convert_numpy_types(obj):
    """Convert NumPy types to native Python types for BSON compatibility"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    elif hasattr(obj, 'item'):  # NumPy scalar
        return obj.item()
    else:
        return obj

def save_user_session(username, file_sessions):
    # Serialize DataFrames and remove non-serializable objects like agents
    session_data = {}
    for fid, session in file_sessions.items():
        # Clean chat history to remove NumPy types
        clean_chat_history = []
        for question, answer in session["chat_history"]:
            # Convert NumPy types to native Python types
            clean_answer = convert_numpy_types(answer)
            clean_chat_history.append((question, clean_answer))
        
        session_data[fid] = {
            "name": session["name"],
            "data_csv": session["df"].to_csv(index=False),
            "chat_history": clean_chat_history
        }
 
    users_collection.update_one(
        {"username": username},
        {"$set": {"file_sessions": session_data}},
        upsert=True
    )

def load_user_session(username):
    user = users_collection.find_one({"username": username})
    file_sessions = {}
    if user and "file_sessions" in user:
        for fid, session in user["file_sessions"].items():
            df = pd.read_csv(StringIO(session["data_csv"]))
            file_sessions[fid] = {
                "name": session["name"],
                "df": df,
                "agent": None,
                "chat_history": session["chat_history"]
            }
    return file_sessions