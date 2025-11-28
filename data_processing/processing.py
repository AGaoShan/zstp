import json
import os
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Tuple, List, Any
import asyncio


from input.md import chunk_md_with_headers
from llm.invoker import extract_audit_insights


def process_single_report(file_path: str, output_dir: str) -> Tuple[str, str]:
    """
    处理单个审计报告文件，并在同步线程中运行异步函数。
    """
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        extracted_knowledge: List[Dict[str, Any]] = []

        # --- 1. 异步分块和提取逻辑 ---

        # 定义一个内部的异步函数来封装异步调用链
        async def run_async_tasks():
            chunks: List[str] = []

            if file_ext == '.md':
                # 传入文件路径给异步分块函数，它在内部处理读取和分块
                # 注意：这里调用的是 await chunk_md_with_headers(file_path)
                chunks = await chunk_md_with_headers(file_path,headers_to_split_on= [("##", "Header 2")])

            elif file_ext == '.txt':
                # 对于 txt 文件，仍需自己同步读取内容，然后作为单个块处理
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    chunks = [content]
                except IOError as e:
                    # 如果txt文件读取失败，立即抛出错误
                    raise IOError(f"Failed to read TXT file: {e}")

            else:
                return []  # 不支持的文件类型，虽然在外层已过滤

            insights = []
            for chunk in chunks:
                # 调用 LLM 提取洞察（假设 extract_audit_insights 也是 async def）
                insight = extract_audit_insights(chunk)
                if insight:
                    insights.append(insight)
            return insights

        # 在当前同步线程中，启动一个临时的事件循环来运行所有异步任务
        # 这就是将异步代码安全地运行在 ThreadPoolExecutor 线程中的关键
        extracted_knowledge = asyncio.run(run_async_tasks())

        # --- 2. 结果保存 (保持同步) ---
        file_name = os.path.basename(file_path)
        output_file = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_result.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_knowledge, f, ensure_ascii=False, indent=2)

        print(f"✅ 成功处理: {file_path}. 提取了 {len(extracted_knowledge)} 条洞察。")
        return file_path, "success"

    except Exception as e:
        # 捕获所有可能的异常，包括由 asyncio.run 内部抛出的异常
        error_msg = f"error: {type(e).__name__}: {str(e)}"
        traceback.print_exc()
        print(f"❌ 处理失败: {file_path}, 错误: {error_msg}")
        return file_path, error_msg



def batch_process_audit_reports(input_dir: str, output_dir: str, max_workers: int = 4) -> Dict[str, str]:
    """
    批量并行处理审计报告
    """
    # ... (代码与您提供的完全一致) ...
    os.makedirs(output_dir, exist_ok=True)

    # 获取所有报告文件，现在支持 .txt 和 .md
    report_files = []
    for file in os.listdir(input_dir):
        # 注意: 如果文件路径是相对的 (如您示例中的 "../audit_reports")，
        # 确保 file 是完整路径，否则内部的 open/chunk_md_with_headers 可能会失败。
        # 您的代码中使用了 os.path.join(input_dir, file)，这是正确的做法。
        if file.endswith(('.txt', '.md')):
            report_files.append(os.path.join(input_dir, file))

    if not report_files:
        print("⚠️ 未找到任何审计报告文件")
        return {}

    # 并行处理文件
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(process_single_report, file, output_dir): file
            for file in report_files
        }

        # 获取结果
        for future in as_completed(future_to_file):
            file_path, status = future.result()
            results[file_path] = status

    # 生成汇总报告
    summary = {
        "total": len(results),
        "success": sum(1 for v in results.values() if v == "success"),
        "failed": sum(1 for v in results.values() if v.startswith("error:"))
    }

    # 保存汇总结果
    try:
        with open(os.path.join(output_dir, "summary.json"), 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ 保存汇总报告失败: {e}")

    print(f"\n📊 处理完成: 总计 {summary['total']} 个文件, 成功 {summary['success']} 个, 失败 {summary['failed']} 个")
    return results


# # 使用示例
# if __name__ == "__main__":
#     # ... (代码与您提供的完全一致) ...
#     INPUT_DIRECTORY = "./audit_reports"  # 存放审计报告的目录
#     OUTPUT_DIRECTORY = "./extracted_knowledge"  # 输出结果的目录
#
#
#     # 执行批量处理
#     results = batch_process_audit_reports(
#         input_dir=INPUT_DIRECTORY,
#         output_dir=OUTPUT_DIRECTORY,
#         max_workers=8  # 根据CPU核心数调整
#     )