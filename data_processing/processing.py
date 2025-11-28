import json
import os
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Tuple, List, Any
import asyncio

from data_processing.vulnerability_entity_alignment import  align_and_ingest_entity
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


def process_single_vulnerability_alignment(json_file_path: str) -> Tuple[str, Dict[str, Any]]:
    """
    处理单个 JSON 文件中的漏洞类型对齐

    Args:
        json_file_path: JSON 文件路径

    Returns:
        Tuple[文件路径, 对齐结果字典]
        对齐结果包含:
        - status: "success" 或 "error"
        - aligned_vulnerabilities: 对齐成功的漏洞列表
        - failed_vulnerabilities: 对齐失败的漏洞列表
        - total_count: 总数
        - success_count: 成功数
        - error_message: 错误信息 (如果有)
    """
    result = {
        "status": "error",
        "aligned_vulnerabilities": [],
        "failed_vulnerabilities": [],
        "total_count": 0,
        "success_count": 0,
        "error_message": None
    }

    try:
        # 读取 JSON 文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            vulnerabilities = json.load(f)

        if not isinstance(vulnerabilities, list):
            result["error_message"] = "JSON 文件格式错误: 应该是列表"
            return json_file_path, result

        result["total_count"] = len(vulnerabilities)

        # 处理每个漏洞
        for idx, vuln_data in enumerate(vulnerabilities):
            try:
                # 检查必需字段
                if 'vulnerability_type' not in vuln_data:
                    result["failed_vulnerabilities"].append({
                        "index": idx,
                        "error": "缺少 vulnerability_type 字段",
                        "original_data": vuln_data
                    })
                    continue

                # 执行实体对齐
                alignment_result = align_and_ingest_entity(vuln_data)

                # 记录对齐成功的漏洞
                result["aligned_vulnerabilities"].append({
                    "index": idx,
                    "original_name": alignment_result['original_name'],
                    "aligned_name": alignment_result['aligned_entity_name'],
                    "action": alignment_result['action'],
                    "similarity": alignment_result.get('similarity'),
                    "entity_id": alignment_result.get('entity_id')
                })
                result["success_count"] += 1

                print(
                    f"  [{idx + 1}/{result['total_count']}] ✓ {alignment_result['original_name']} -> {alignment_result['aligned_entity_name']}")

            except Exception as e:
                # 记录对齐失败的漏洞
                error_msg = f"{type(e).__name__}: {str(e)}"
                result["failed_vulnerabilities"].append({
                    "index": idx,
                    "error": error_msg,
                    "original_data": vuln_data
                })
                print(f"  [{idx + 1}/{result['total_count']}] ✗ 对齐失败: {error_msg}")

        # 如果有成功的对齐，则整体状态为成功
        if result["success_count"] > 0:
            result["status"] = "success"

        print(f"✅ 文件处理完成: {json_file_path} - 成功 {result['success_count']}/{result['total_count']}")
        return json_file_path, result

    except Exception as e:
        result["error_message"] = f"{type(e).__name__}: {str(e)}"
        traceback.print_exc()
        print(f"❌ 文件处理失败: {json_file_path} - {result['error_message']}")
        return json_file_path, result


def batch_process_vulnerability_alignment(output_dir: str, max_workers: int = 4) -> Dict[str, Any]:
    """
    批量并行处理输出目录中的 JSON 文件，执行漏洞类型对齐

    Args:
        output_dir: 包含 JSON 结果文件的目录
        max_workers: 最大并行工作线程数

    Returns:
        Dict: 包含处理结果的汇总信息
    """
    print(f"\n{'=' * 60}")
    print(f"开始批量处理漏洞类型对齐")
    print(f"目录: {output_dir}")
    print(f"{'=' * 60}\n")

    # 获取所有 JSON 结果文件 (排除 summary.json)
    json_files = []
    for file in os.listdir(output_dir):
        if file.endswith('_result.json') and file != 'summary.json':
            json_files.append(os.path.join(output_dir, file))

    if not json_files:
        print("⚠️ 未找到任何结果 JSON 文件")
        return {
            "total_files": 0,
            "processed_files": 0,
            "total_vulnerabilities": 0,
            "aligned_vulnerabilities": 0,
            "failed_vulnerabilities": 0
        }

    print(f"找到 {len(json_files)} 个 JSON 文件\n")

    # 并行处理文件
    alignment_results = {}
    total_vulnerabilities = 0
    total_aligned = 0
    total_failed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(process_single_vulnerability_alignment, file): file
            for file in json_files
        }

        # 获取结果
        for future in as_completed(future_to_file):
            file_path, result = future.result()
            alignment_results[file_path] = result

            # 累计统计
            total_vulnerabilities += result["total_count"]
            total_aligned += result["success_count"]
            total_failed += len(result["failed_vulnerabilities"])

    # 生成汇总报告
    summary = {
        "total_files": len(json_files),
        "processed_files": len(alignment_results),
        "successful_files": sum(1 for r in alignment_results.values() if r["status"] == "success"),
        "failed_files": sum(1 for r in alignment_results.values() if r["status"] == "error"),
        "total_vulnerabilities": total_vulnerabilities,
        "aligned_vulnerabilities": total_aligned,
        "failed_vulnerabilities": total_failed,
        "alignment_rate": f"{(total_aligned / total_vulnerabilities * 100):.2f}%" if total_vulnerabilities > 0 else "0%",
        "details": {}
    }

    # 添加每个文件的详细信息
    for file_path, result in alignment_results.items():
        file_name = os.path.basename(file_path)
        summary["details"][file_name] = {
            "status": result["status"],
            "total": result["total_count"],
            "aligned": result["success_count"],
            "failed": len(result["failed_vulnerabilities"]),
            "error_message": result.get("error_message")
        }

    # 保存汇总结果
    alignment_summary_path = os.path.join(output_dir, "alignment_summary.json")
    try:
        with open(alignment_summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\n💾 对齐汇总已保存至: {alignment_summary_path}")
    except Exception as e:
        print(f"❌ 保存对齐汇总失败: {e}")

    # 保存详细的对齐结果
    detailed_results_path = os.path.join(output_dir, "alignment_detailed_results.json")
    try:
        with open(detailed_results_path, 'w', encoding='utf-8') as f:
            json.dump(alignment_results, f, ensure_ascii=False, indent=2)
        print(f"💾 详细对齐结果已保存至: {detailed_results_path}")
    except Exception as e:
        print(f"❌ 保存详细对齐结果失败: {e}")

    # 打印汇总信息
    print(f"\n{'=' * 60}")
    print(f"📊 漏洞类型对齐完成")
    print(f"{'=' * 60}")
    print(f"处理文件: {summary['processed_files']}/{summary['total_files']}")
    print(f"总漏洞数: {summary['total_vulnerabilities']}")
    print(f"对齐成功: {summary['aligned_vulnerabilities']} ({summary['alignment_rate']})")
    print(f"对齐失败: {summary['failed_vulnerabilities']}")
    print(f"{'=' * 60}\n")

    return summary

#使用示例

# ... (代码与您提供的完全一致) ...
INPUT_DIRECTORY = "./audit_reports"  # 存放审计报告的目录
OUTPUT_DIRECTORY = "./extracted_knowledge"  # 输出结果的目录
#
#
#     # 执行批量处理
#     results = batch_process_audit_reports(
#         input_dir=INPUT_DIRECTORY,
#         output_dir=OUTPUT_DIRECTORY,
#         max_workers=8  # 根据CPU核心数调整
#     )
batch_process_vulnerability_alignment(OUTPUT_DIRECTORY)