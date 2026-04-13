#!/usr/bin/env python3
"""
重新创建 document_chunks 集合以支持混合检索
"""

import sys
import os

project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

from backend.milvus.client import get_milvus_client
from pymilvus import utility


def recreate_document_chunks():
    """重新创建 document_chunks 集合"""
    print("=" * 60)
    print("重新创建 document_chunks 集合")
    print("=" * 60)

    client = get_milvus_client()
    collection_name = "document_chunks"

    # 检查集合是否存在
    collections = client.list_collections()
    print(f"\n现有集合: {collections}")

    if collection_name in collections:
        print(f"\n删除旧集合: {collection_name}")
        utility.drop_collection(collection_name)
        print("[OK] 旧集合已删除")

    # 创建新集合
    print(f"\n创建新集合: {collection_name}")
    client.create_collection(collection_name, dimension=1024)
    print("[OK] 新集合创建成功")

    # 验证
    stats = client.get_collection_stats(collection_name)
    print(f"\n集合信息:")
    print(f"  - 存在: {stats.get('exists', False)}")
    print(f"  - 记录数: {stats.get('count', 0)}")

    from pymilvus import Collection

    collection = Collection(collection_name)
    fields = [f.name for f in collection.schema.fields]
    print(f"  - 字段: {fields}")

    if "sparse_embedding" in fields:
        print("\n[OK] 集合已支持稀疏向量 - 混合检索就绪！")
    else:
        print("\n[FAIL] 集合不支持稀疏向量")

    print("\n" + "=" * 60)
    print("重要提示：")
    print("  集合已重新创建，原有数据已清空")
    print("  请重新上传文档以建立混合索引")
    print("=" * 60)


if __name__ == "__main__":
    from dotenv import load_dotenv

    env_path = os.path.join(project_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)

    recreate_document_chunks()
