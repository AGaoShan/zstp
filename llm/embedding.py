import logging
import os
from openai import OpenAI
from typing import List, Dict, Union, Optional

# --- 配置 ---
logger = logging.getLogger(__name__)

# ⚠️ 实际使用时，请将 API Key 和 BASE_URL 设为环境变量
API_KEY = "sk-Umy6QJiK8EY6Aco8EbriaMB1cw2nq15bY6y8OBM8mJUQTxcr"
EMBEDDING_MODEL = "text-embedding-3-small"
BASE_URL = "https://yunwu.ai/v1"

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def get_embedding(
    text: Union[str, List[str]],
    model: str = EMBEDDING_MODEL,
    dimensions: Optional[int] = 768
) -> List[List[float]]:
    if not text:
        return []

    # 检查模型是否支持维度调整
    if dimensions is not None and not model.startswith("text-embedding-3-"):
        logger.warning(f"⚠️ 模型 {model} 可能不支持 'dimensions' 参数。")

    log_msg = f"✅ 正在调用 API 使用模型：{model}"
    if dimensions is not None:
        log_msg += f"，目标维度：{dimensions}"
    logger.info(log_msg)

    try:
        # 构造请求参数
        params = {
            "input": text,
            "model": model,
        }
        # 只有当 dimensions 不为空时才添加到请求中
        if dimensions is not None:
            params["dimensions"] = dimensions

        response = client.embeddings.create(**params)

        embeddings = [data.embedding for data in response.data]
        return embeddings
    except Exception as e:
        logger.warning(f"❌ 调用 API 发生错误: {e}")
        return []

# # --- 示例使用 ---
# if __name__ == "__main__":
#     text_to_embed = "实现高效且低维度的文本表示，对于提高检索速度非常关键。"
#
#     # 1. 默认维度 (text-embedding-3-small 默认 1536 维)
#     print("\n--- 1. 默认维度 Embedding ---")
#     default_embedding = get_embedding(text_to_embed)
#
#     if default_embedding:
#         print(f"默认 Embedding 维度: **{len(default_embedding[0])}**")
#         print(f"向量前5个元素: {default_embedding[0][:5]}...")
#
#     # 2. 调整维度到 256
#     print("\n--- 2. 调整维度到 256 ---")
#     custom_embedding_256 = get_embedding(text_to_embed, dimensions=256)
#
#     if custom_embedding_256:
#         print(f"256 维 Embedding 维度: **{len(custom_embedding_256[0])}**")
#         print(f"向量前5个元素: {custom_embedding_256[0][:5]}...")
#
#     # 3. 调整维度到 768
#     print("\n--- 3. 调整维度到 768 ---")
#     custom_embedding_768 = get_embedding(text_to_embed, dimensions=768)
#
#     if custom_embedding_768:
#         print(f"768 维 Embedding 维度: **{len(custom_embedding_768[0])}**")
#         print(f"向量前5个元素: {custom_embedding_768[0][:5]}...")