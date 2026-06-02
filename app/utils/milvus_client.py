from pymilvus import MilvusClient
from app.core.config import get_settings

settings = get_settings()
_client = None


def get_milvus_client() -> MilvusClient:
    global _client
    if _client is None:
        _client = MilvusClient(uri=f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
    return _client


def disconnect_milvus():
    global _client
    if _client:
        _client.close()
        _client = None


def get_knowledge_collection() -> str:
    return settings.MILVUS_COLLECTION
