#!/usr/bin/env python3
"""
文档导入脚本 - 将文档导入到 RAG 知识库

使用方法:
    # 导入单个文件
    python ingest.py --file path/to/document.pdf

    # 导入整个目录
    python ingest.py --dir path/to/documents/ --pattern "**/*.md"

    # 带自定义元数据
    python ingest.py --file doc.pdf --meta '{"category": "技术文档", "project": "AI"}'

    # 查看统计信息
    python ingest.py --stats

    # 删除指定来源的文档
    python ingest.py --delete-source "path/to/doc.pdf"
"""

import argparse
import json
import sys
from pathlib import Path

from document_processor import process_and_store, DocumentProcessor, DocumentStore
from database_milvus_client import get_milvus_client


def main():
    parser = argparse.ArgumentParser(
        description="将文档导入 RAG 知识库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python ingest.py --file document.pdf
  python ingest.py --dir ./docs/ --pattern "**/*.md"
  python ingest.py --file doc.txt --chunk-size 500 --overlap 100
  python ingest.py --stats
  python ingest.py --delete-source "./old_doc.pdf"
        """,
    )

    # 输入选项
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--file", "-f", help="要导入的单个文件路径")
    input_group.add_argument("--dir", "-d", help="要导入的目录路径")
    input_group.add_argument(
        "--stats", "-s", action="store_true", help="显示知识库统计信息"
    )
    input_group.add_argument(
        "--delete-source", metavar="SOURCE", help="删除指定来源的所有文档"
    )

    # 处理参数
    parser.add_argument(
        "--pattern", "-p", default="**/*", help="文件匹配模式 (默认: **/*)"
    )
    parser.add_argument(
        "--chunk-size", "-c", type=int, default=1000, help="分块大小 (默认: 1000)"
    )
    parser.add_argument(
        "--overlap", "-o", type=int, default=200, help="块重叠大小 (默认: 200)"
    )
    parser.add_argument(
        "--meta", "-m", help='自定义元数据 (JSON格式, 如: \'{"key": "value"}\')'
    )
    parser.add_argument(
        "--batch-size", "-b", type=int, default=100, help="批处理大小 (默认: 100)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="试运行模式（只处理不存储）"
    )

    args = parser.parse_args()

    # 显示统计信息
    if args.stats:
        show_stats()
        return

    # 删除文档
    if args.delete_source:
        delete_by_source(args.delete_source)
        return

    # 检查输入
    if not args.file and not args.dir:
        parser.error("必须指定 --file 或 --dir")

    # 解析元数据
    custom_metadata = {}
    if args.meta:
        try:
            custom_metadata = json.loads(args.meta)
        except json.JSONDecodeError as e:
            print(f"错误: 元数据 JSON 格式无效: {e}")
            sys.exit(1)

    # 执行导入
    try:
        if args.dry_run:
            print("【试运行模式】不会实际存储数据\n")

        print("=" * 60)
        print("文档导入工具")
        print("=" * 60)
        print(f"分块大小: {args.chunk_size}")
        print(f"重叠大小: {args.overlap}")
        print(f"批处理大小: {args.batch_size}")
        if custom_metadata:
            print(f"自定义元数据: {custom_metadata}")
        print("-" * 60)

        if args.dry_run:
            # 试运行 - 只处理不存储
            processor = DocumentProcessor(
                chunk_size=args.chunk_size,
                chunk_overlap=args.overlap,
                batch_size=args.batch_size,
            )

            if args.file:
                chunks = processor.process_file(args.file, custom_metadata)
            else:
                chunks = processor.process_directory(
                    args.dir, args.pattern, custom_metadata
                )

            print(f"\n试运行结果:")
            print(f"  处理文档块数: {len(chunks)}")
            if chunks:
                print(f"  示例块内容: {chunks[0].content[:100]}...")
                print(f"  示例块ID: {chunks[0].chunk_id}")
        else:
            # 实际导入
            result = process_and_store(
                file_path=args.file,
                directory=args.dir,
                custom_metadata=custom_metadata,
                chunk_size=args.chunk_size,
                chunk_overlap=args.overlap,
            )

            print("\n" + "=" * 60)
            print("导入完成!")
            print("=" * 60)
            print(f"处理文档块数: {result['processed_chunks']}")
            print(f"成功存储: {result['stored_count']}")

            if result["errors"]:
                print(f"\n警告: 有 {len(result['errors'])} 个错误:")
                for error in result["errors"][:5]:  # 只显示前5个
                    print(f"  - {error}")

    except FileNotFoundError as e:
        print(f"错误: 文件或目录不存在 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


def show_stats():
    """显示知识库统计信息"""
    print("=" * 60)
    print("知识库统计信息")
    print("=" * 60)

    try:
        client = get_milvus_client()

        # 列出所有集合
        collections = client.list_collections()
        print(f"\n向量集合列表:")
        for name in collections:
            stats = client.get_collection_stats(name)
            print(f"  - {name}")
            if stats.get("exists"):
                print(f"    文档数: {stats.get('count', 'N/A')}")

    except Exception as e:
        print(f"获取统计信息失败: {e}")


def delete_by_source(source: str):
    """删除指定来源的文档"""
    print("=" * 60)
    print("删除文档")
    print("=" * 60)
    print(f"来源: {source}")

    confirm = input("\n确认删除? (yes/no): ")
    if confirm.lower() != "yes":
        print("已取消")
        return

    try:
        client = get_milvus_client()
        deleted = client.delete_by_source("document_chunks", source)
        print(f"已删除 {deleted} 条记录")
    except Exception as e:
        print(f"删除失败: {e}")


if __name__ == "__main__":
    main()
