import logging
from pathlib import Path
import asyncio
from typing import List, Dict

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import MarkdownHeaderTextSplitter

logger = logging.getLogger(__name__)

async def load_md(
    path: str
) -> str | None:
    """
    load md
    """
    p = Path(path)

    if not p.exists():
        logger.error(f"文件不存在: {path}")
        return None

    if p.is_dir():
        logger.error(f"路径 {path} 是一个目录，不是文件。")
        return None

    def _read_file_sync():
        try:
            return p.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"读取文件 {path} 失败: {e}")
            return None
    content = await asyncio.to_thread(_read_file_sync)

    if content is not None:
        logger.info(f"成功加载文件: {path}，内容长度 {len(content)}。")
    
    return content


async def chunk_md_file(
        path: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
) -> List[str]:
    """
    加载 Markdown 文件并使用递归字符分片器进行分片。

    :param path: Markdown 文件路径。
    :param chunk_size: 每个分块的最大字符数。
    :param chunk_overlap: 分块间的重叠字符数，用于保持上下文。
    :return: 包含所有文本分块的列表。
    """
    logger.info(f"开始加载文件: {path}")
    markdown_text = await load_md(path)

    if not markdown_text:
        logger.warning(f"无法加载或文件内容为空: {path}")
        return []

    # 1. 初始化分片器
    # RecursiveCharacterTextSplitter 默认的分隔符列表是：
    # ["\n\n", "\n", " ", ""]，它会优先尝试按段落、然后按行、最后按空格切分。
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,  # 使用 Python 内建的 len 函数计算长度
    )

    # 2. 执行分片
    logger.info(f"开始分片，Chunk Size: {chunk_size}, Overlap: {chunk_overlap}")
    chunks: List[str] = text_splitter.split_text(markdown_text)

    logger.info(f"分片完成。总共生成了 {len(chunks)} 个分块。")
    return chunks





async def chunk_md_with_headers(
        path: str,
        headers_to_split_on: List[tuple] = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
) -> List[Dict]:
    """
    根据 Markdown 标题结构进行分片，并保留每个分块的元数据 (Metadata)。
    :param path: Markdown 文件路径。
    :param headers_to_split_on: 用于结构化切分的标题级别。
    :return: 包含分块内容和元数据 (如 'Header 1' 的值) 的字典列表。
    """
    markdown_text = await load_md(path)
    if not markdown_text:
        return []

    # 1. 初始化 Markdown 结构分片器
    # 它首先按标题切分文档
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )
    docs = markdown_splitter.split_text(markdown_text)
    final_chunks = []
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    for doc in docs:
        # sub_chunks = text_splitter.split_text(doc.page_content)
        chunk_dict = {
                "content": doc.page_content,
                "metadata": doc.metadata
        }
        final_chunks.append(chunk_dict)

    logger.info(f"Markdown 结构化分片完成。总共生成了 {len(final_chunks)} 个分块。")
    return final_chunks




##test

#logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# async def main():
#     chunks = await chunk_md_with_headers("test.md",headers_to_split_on= [("##", "Header 2")])
#     for chunk in chunks:
#         print(chunk["metadata"],"\n")
#         print(chunk["content"])
#         print("***" * 50)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())