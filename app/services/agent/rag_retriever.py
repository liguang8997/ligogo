"""
RAG 知识库检索器
将用户问题向量化 → Milvus 搜索 → 返回相关文档片段
"""
from openai import OpenAI
from app.core.config import get_settings
from app.utils.milvus_client import get_milvus_client, get_knowledge_collection

settings = get_settings()


class RAGRetriever:
    def __init__(self):
        self.emb_client = OpenAI(
            base_url=settings.EMBEDDING_BASE_URL,
            api_key=settings.EMBEDDING_API_KEY,
        )
        self.milvus = get_milvus_client()
        self.collection = get_knowledge_collection()

    async def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """检索与查询最相关的文档片段"""
        # 向量化查询
        resp = self.emb_client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=query,
            dimensions=1024,
        )
        query_vec = resp.data[0].embedding

        # Milvus 搜索
        results = self.milvus.search(
            collection_name=self.collection,
            data=[query_vec],
            limit=top_k,
            output_fields=["title", "content"],
        )

        docs = []
        for hits in results:
            for hit in hits:
                docs.append({
                    "title": hit.get("entity", {}).get("title", ""),
                    "content": hit.get("entity", {}).get("content", ""),
                    "score": round(hit.get("distance", 0), 4),
                })
        return docs

    def format_context(self, docs: list[dict]) -> str:
        """将检索结果格式化为 LLM 上下文"""
        parts = []
        for i, doc in enumerate(docs, 1):
            parts.append(f"[文档{i}] {doc['title']}\n{doc['content']}")
        return "\n\n".join(parts)
