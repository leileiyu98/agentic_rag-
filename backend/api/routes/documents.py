"""Document Routes - 文档管理相关 API 接口"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import Optional
import traceback
import os
import tempfile
import shutil

from backend.api.models import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    DocumentStatsResponse,
    DeleteDocumentRequest,
    DeleteDocumentResponse,
    CollectionStats,
)
from backend.src.document_processor import process_and_store
from backend.milvus.client import get_milvus_client

router = APIRouter(prefix="/documents", tags=["文档管理"])


@router.post("/ingest", response_model=DocumentIngestResponse, summary="导入文档")
async def ingest_documents(request: DocumentIngestRequest):
    """
    导入文档到知识库

    - 支持单个文件或整个目录
    - 可以自定义分块大小和重叠
    - 支持添加自定义元数据
    """
    # 验证请求
    if not request.file_path and not request.directory:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供 file_path 或 directory",
        )

    if request.file_path and request.directory:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能同时提供 file_path 和 directory",
        )

    try:
        # 调用处理器
        result = process_and_store(
            file_path=request.file_path,
            directory=request.directory,
            custom_metadata=request.metadata,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )

        return DocumentIngestResponse(
            success=len(result.get("errors", [])) == 0,
            processed_chunks=result.get("processed_chunks", 0),
            stored_count=result.get("stored_count", 0),
            errors=result.get("errors", []),
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"文件或目录不存在: {str(e)}",
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败: {str(e)}",
        )


@router.get("/stats", response_model=DocumentStatsResponse, summary="获取文档统计")
async def get_document_stats():
    """
    获取知识库统计信息

    - 返回所有向量集合的统计
    - 包括文档数量和集合信息
    """
    try:
        client = get_milvus_client()
        collections = client.list_collections()

        stats = []
        for name in collections:
            collection_stats = client.get_collection_stats(name)
            stats.append(
                CollectionStats(
                    exists=collection_stats.get("exists", False),
                    name=name,
                    count=collection_stats.get("count"),
                )
            )

        return DocumentStatsResponse(
            success=True,
            collections=stats,
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计失败: {str(e)}",
        )


@router.post("/delete", response_model=DeleteDocumentResponse, summary="删除文档")
async def delete_documents(request: DeleteDocumentRequest):
    """
    删除指定来源的文档

    - 根据 source 字段删除所有相关文档块
    - 请谨慎使用，删除后不可恢复
    """
    try:
        client = get_milvus_client()
        deleted_count = client.delete_by_source("document_chunks", request.source)

        message = f"成功删除 {deleted_count} 条记录"
        if deleted_count == 0:
            message = "未找到匹配的文档"

        return DeleteDocumentResponse(
            success=True,
            deleted_count=deleted_count,
            message=message,
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}",
        )


@router.post("/clear/{collection_name}", summary="清空集合")
async def clear_collection(collection_name: str):
    """
    清空指定集合的所有文档

    - 删除集合中的所有数据
    - 请谨慎使用，删除后不可恢复
    """
    try:
        print(f"[DEBUG] Clear collection request: {collection_name}")
        client = get_milvus_client()

        # 先检查集合状态
        stats_before = client.get_collection_stats(collection_name)
        print(f"[DEBUG] Stats before clear: {stats_before}")

        deleted_count = client.clear_collection(collection_name)

        # 再检查集合状态
        stats_after = client.get_collection_stats(collection_name)
        print(f"[DEBUG] Stats after clear: {stats_after}")

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"成功清空集合 {collection_name}，删除 {deleted_count} 条记录",
        }

    except Exception as e:
        print(f"[ERROR] Clear collection failed: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空失败: {str(e)}",
        )


@router.get("/sources/{collection_name}", summary="获取集合的文档来源列表")
async def get_collection_sources(collection_name: str):
    """
    获取指定集合中所有文档的来源列表

    - 返回去重后的 source 列表
    """
    try:
        client = get_milvus_client()
        sources = client.get_sources(collection_name)

        return {
            "success": True,
            "collection": collection_name,
            "sources": sources,
            "total": len(sources),
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取来源列表失败: {str(e)}",
        )


@router.get("/collections", summary="列出所有集合")
async def list_collections():
    """
    列出所有向量集合
    """
    try:
        client = get_milvus_client()
        collections = client.list_collections()

        return {
            "success": True,
            "collections": collections,
            "total": len(collections),
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取集合列表失败: {str(e)}",
        )


@router.post("/upload", response_model=DocumentIngestResponse, summary="上传并导入文档")
async def upload_document(
    file: UploadFile = File(..., description="要上传的文档文件"),
    chunk_size: int = Form(default=1000, ge=100, le=5000, description="分块大小"),
    chunk_overlap: int = Form(default=200, ge=0, le=1000, description="重叠大小"),
):
    """
    上传文件并导入到知识库

    - 支持 .pdf, .docx, .txt, .md 等格式
    - 文件临时存储，处理完成后自动删除
    - 可以自定义分块大小和重叠
    """
    # 检查文件类型
    allowed_extensions = {
        ".pdf",
        ".docx",
        ".doc",
        ".txt",
        ".md",
        ".json",
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
    }
    file_ext = os.path.splitext(file.filename.lower())[1]

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(allowed_extensions)}",
        )

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)

    try:
        # 保存上传的文件
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 调用处理器
        result = process_and_store(
            file_path=temp_file_path,
            custom_metadata={"original_filename": file.filename, "uploaded": True},
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        return DocumentIngestResponse(
            success=len(result.get("errors", [])) == 0,
            processed_chunks=result.get("processed_chunks", 0),
            stored_count=result.get("stored_count", 0),
            errors=result.get("errors", []),
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理失败: {str(e)}",
        )
    finally:
        # 清理临时文件
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
