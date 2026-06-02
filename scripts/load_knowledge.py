"""
学校信息向量化脚本
将学校信息.txt 分块向量化后存入 Milvus
(PyMilvus 3.0 compatible)
"""
import io
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from openai import OpenAI
from pymilvus import MilvusClient, DataType
from pymilvus.milvus_client.index import IndexParams

# ======== 配置 ========
EMBEDDING_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
EMBEDDING_API_KEY = "sk-d716ce5d91f04563b2345e4ca19e64f2"
EMBEDDING_MODEL = "text-embedding-v3"
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "teacher_school_knowledge"
DIMENSION = 1024

SCHOOL_INFO_PATH = Path(__file__).parent.parent.parent / "学校信息.txt"

client = OpenAI(base_url=EMBEDDING_BASE_URL, api_key=EMBEDDING_API_KEY)
milvus = MilvusClient(uri=f"http://{MILVUS_HOST}:{MILVUS_PORT}")


def read_and_chunk(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = []
    sections = content.split("\n### ")

    for section in sections:
        section = section.strip()
        if not section:
            continue
        lines = section.split("\n")
        title_line = lines[0].lstrip("#").strip()
        text = section

        if len(text) > 2000:
            paragraphs = text.split("\n\n")
            current_chunk = ""
            for para in paragraphs:
                if len(current_chunk) + len(para) < 1500:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk.strip():
                        chunks.append({"title": title_line, "content": current_chunk.strip()})
                    current_chunk = para + "\n\n"
            if current_chunk.strip():
                chunks.append({"title": title_line, "content": current_chunk.strip()})
        else:
            chunks.append({"title": title_line, "content": text})

    return chunks


def get_embedding(text: str) -> list[float]:
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=text, dimensions=DIMENSION)
    return resp.data[0].embedding


def setup_milvus():
    if milvus.has_collection(COLLECTION_NAME):
        milvus.drop_collection(COLLECTION_NAME)

    schema = milvus.create_schema(auto_id=True, enable_dynamic_field=False)
    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=DIMENSION)
    schema.add_field("title", DataType.VARCHAR, max_length=200)
    schema.add_field("content", DataType.VARCHAR, max_length=4000)

    milvus.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
    )
    print(f"[OK] Collection '{COLLECTION_NAME}' created, dim={DIMENSION}")


def main():
    print("=" * 60)
    print("  学校信息向量化入库 (PyMilvus 3.0)")
    print("=" * 60)

    print(f"\n[1/4] Reading: {SCHOOL_INFO_PATH}")
    chunks = read_and_chunk(str(SCHOOL_INFO_PATH))
    print(f"       Total chunks: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"       [{i}] {c['title'][:50]}... ({len(c['content'])} chars)")

    print(f"\n[2/4] Setting up Milvus collection...")
    setup_milvus()

    print(f"\n[3/4] Vectorizing and inserting...")
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        text_to_embed = chunk["content"][:4000]
        print(f"       [{i+1}/{total}] Embedding: {chunk['title'][:40]}...", end=" ", flush=True)

        try:
            vector = get_embedding(text_to_embed)
        except Exception as e:
            print(f"ERROR: {e}")
            time.sleep(2)
            try:
                vector = get_embedding(text_to_embed)
            except Exception as e2:
                print(f"SKIPPED (retry failed)")
                continue

        milvus.insert(
            collection_name=COLLECTION_NAME,
            data=[{
                "vector": vector,
                "title": chunk["title"][:200],
                "content": chunk["content"][:4000],
            }],
        )
        print(f"OK (dim={len(vector)})", flush=True)
        time.sleep(0.5)

    print(f"\n[4/4] Creating index & loading...")
    idx_params = IndexParams()
    idx_params.add_index(field_name="vector", index_type="IVF_FLAT", metric_type="IP", params={"nlist": 64})
    milvus.create_index(collection_name=COLLECTION_NAME, index_params=idx_params)
    milvus.load_collection(COLLECTION_NAME)

    stats = milvus.get_collection_stats(COLLECTION_NAME)
    print(f"[DONE] Total vectors: {stats['row_count']}")


if __name__ == "__main__":
    main()
