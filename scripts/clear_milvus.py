#!/usr/bin/env python3
"""
清空 Milvus 向量数据库中的所有数据
用于升级到混合检索前的数据清理
"""

import sys
import os

# 设置无缓冲输出
sys.stdout.reconfigure(line_buffering=True)

# 添加项目根目录到路径
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

from backend.milvus.client import get_milvus_client, MilvusClientWrapper

# 要清空的集合列表
COLLECTIONS_TO_CLEAR = [
    "document_chunks",  # 主文档集合
    "test_collection",  # 测试集合（如果存在）
]


def clear_all_collections():
    """清空所有集合数据"""
    print("=" * 60)
    print("Milvus 数据清理工具")
    print("=" * 60)

    # 获取客户端
    client = get_milvus_client()

    # 列出所有集合
    all_collections = client.list_collections()
    print(f"\n当前 Milvus 中的所有集合: {all_collections}")

    if not all_collections:
        print("\n没有需要清理的集合")
        return

    # 统计信息
    print("\n" + "-" * 60)
    print("各集合统计信息:")
    total_records = 0
    for collection_name in all_collections:
        stats = client.get_collection_stats(collection_name)
        count = stats.get("count", 0)
        total_records += count
        print(f"  - {collection_name}: {count} 条记录")
    print("-" * 60)
    print(f"总计: {total_records} 条记录")
    print("-" * 60)

    # 确认提示
    print("\n[!] 警告: 此操作将永久删除以上所有集合中的数据!")
    confirm = input("\n确认清空所有数据? 请输入 'yes' 继续: ")

    if confirm.lower() != "yes":
        print("\n操作已取消")
        return

    # 执行清空
    print("\n" + "=" * 60)
    print("开始清空数据...")
    print("=" * 60)

    total_deleted = 0
    for collection_name in all_collections:
        print(f"\n正在清空集合: {collection_name}")
        try:
            deleted = client.clear_collection(collection_name)
            total_deleted += deleted
            print(f"[OK] 集合 {collection_name} 已清空，删除 {deleted} 条记录")
        except Exception as e:
            print(f"[FAIL] 清空集合 {collection_name} 失败: {e}")

    print("\n" + "=" * 60)
    print(f"清理完成! 共删除 {total_deleted} 条记录")
    print("=" * 60)

    # 验证清空结果
    print("\n验证清空结果:")
    for collection_name in all_collections:
        stats = client.get_collection_stats(collection_name)
        count = stats.get("count", 0)
        status = "[OK] 已清空" if count == 0 else f"[WARN] 仍有 {count} 条记录"
        print(f"  - {collection_name}: {status}")


def clear_specific_collection(collection_name: str):
    """清空指定集合"""
    print(f"\n清空指定集合: {collection_name}")

    client = get_milvus_client()

    # 检查集合是否存在
    all_collections = client.list_collections()
    if collection_name not in all_collections:
        print(f"集合 {collection_name} 不存在")
        return

    # 获取统计
    stats = client.get_collection_stats(collection_name)
    count = stats.get("count", 0)
    print(f"集合 {collection_name} 当前有 {count} 条记录")

    if count == 0:
        print("集合已经是空的")
        return

    # 确认
    confirm = input(f"确认清空 {collection_name}? 请输入 'yes' 继续: ")
    if confirm.lower() != "yes":
        print("操作已取消")
        return

    # 清空
    deleted = client.clear_collection(collection_name)
    print(f"[OK] 已删除 {deleted} 条记录")


if __name__ == "__main__":
    # 加载环境变量
    from dotenv import load_dotenv

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"已加载环境变量: {env_path}")

    # 解析命令行参数
    if len(sys.argv) > 1:
        collection_name = sys.argv[1]
        clear_specific_collection(collection_name)
    else:
        clear_all_collections()
