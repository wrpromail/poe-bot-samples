import asyncio

from google.cloud import firestore

db = firestore.AsyncClient()
coll_name = "default-firestore"

def echo_log_data(message_id:str, user_input: str):
    return {"message_id": message_id,"content": user_input, "timestamp": firestore.SERVER_TIMESTAMP, "type": "echo_text"}

async def add_data(message_id: str, user_input:str, action_log):
    doc_ref = db.collection(coll_name).document()
    await doc_ref.set(action_log(message_id, user_input))

