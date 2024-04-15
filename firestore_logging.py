from google.cloud import firestore
import logging

class FirestoreLogger:
    def __init__(self):
        self.db = None
        self.open_logging = False
        self.initialize_client()

    def initialize_client(self):
        try:
            self.db = firestore.AsyncClient()
            self.open_logging = True
        except Exception as e:
            logging.error(f"初始化 Firestore 客户端失败: {e}")

    async def add_data(self, message_id: str, user_input: str, action_log):
        if not self.open_logging or self.db is None:
            logging.info("日志记录未启用或客户端未初始化。")
            return

        doc_ref = self.db.collection("default-firestore").document()

        try:
            log_data = action_log(message_id, user_input)
            await doc_ref.set(log_data)
        except Exception as e:
            logging.error(f"添加数据失败: {e}")

def echo_log_data(message_id: str, user_input: str):
    return {
        "message_id": message_id,
        "content": user_input,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "type": "echo_text"
    }