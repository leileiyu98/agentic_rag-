"""FastAPI Main Application - RAG Agent API 服务"""

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import chat, documents


# ==================== 生命周期管理 ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    - 启动时: 初始化数据库表、检查服务连接
    - 关闭时: 清理资源
    """
    # 启动时执行
    print("=" * 60)
    print("RAG Agent API 服务启动中...")
    print("=" * 60)

    try:
        # 确保数据库表存在
        from backend.db.models.base import Base
        from backend.db.connection import DatabaseConnection

        db = DatabaseConnection()
        Base.metadata.create_all(bind=db.engine)
        print("[OK] 数据库表检查完成")

        # 检查 Milvus 连接
        from backend.milvus.client import get_milvus_client

        client = get_milvus_client()
        collections = client.list_collections()
        print(f"[OK] Milvus 连接正常 ({len(collections)} 个集合)")

        # 检查环境变量
        import os

        if not os.getenv("OPENAI_API_KEY"):
            print("[WARN] OPENAI_API_KEY 环境变量未设置")
        else:
            print("[OK] OpenAI API Key 已配置")

        print("\n[SUCCESS] 服务启动完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 启动检查失败: {e}")
        print("=" * 60)

    yield

    # 关闭时执行
    print("\n" + "=" * 60)
    print("RAG Agent API 服务关闭中...")
    print("=" * 60)


# ==================== 创建 FastAPI 应用 ====================


app = FastAPI(
    title="RAG Agent API",
    description="基于 LangGraph 的智能 RAG Agent 系统 API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI 路径
    redoc_url="/redoc",  # ReDoc 路径
    openapi_url="/openapi.json",
)


# ==================== 中间件 ====================


# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    记录所有请求的日志
    """
    # 生成请求ID
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    # 记录开始时间
    start_time = time.time()

    # 获取请求信息
    method = request.method
    path = request.url.path

    print(f"[{request_id}] → {method} {path}")

    try:
        # 处理请求
        response = await call_next(request)

        # 计算耗时
        process_time = time.time() - start_time

        # 添加自定义响应头
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        # 记录响应
        status_code = response.status_code
        print(f"[{request_id}] ← {status_code} ({process_time:.3f}s)")

        return response

    except Exception as e:
        process_time = time.time() - start_time
        print(f"[{request_id}] ← ERROR ({process_time:.3f}s): {e}")
        raise


# 错误处理中间件
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理
    """
    request_id = getattr(request.state, "request_id", "unknown")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "服务器内部错误",
            "detail": str(exc),
            "request_id": request_id,
        },
    )


# ==================== 路由注册 ====================


# 注册聊天相关路由
app.include_router(chat.router)

# 注册文档管理路由
app.include_router(documents.router)


# ==================== 根路由 ====================


@app.get("/", summary="API 根路径")
async def root():
    """
    API 根路径，返回基本信息
    """
    return {
        "name": "RAG Agent API",
        "version": "1.0.0",
        "description": "基于 LangGraph 的智能 RAG Agent 系统",
        "docs": "/docs",
        "endpoints": {
            "chat": "/chat/",
            "documents": "/documents/",
        },
    }


@app.get("/health", summary="健康检查")
async def health_check():
    """
    健康检查接口

    返回服务状态和依赖服务连接情况
    """
    status = {
        "status": "healthy",
        "services": {},
    }

    # 检查数据库
    try:
        from backend.db.connection import DatabaseConnection
        from sqlalchemy import text

        db = DatabaseConnection()
        session = db.get_session()
        session.execute(text("SELECT 1"))
        session.close()
        status["services"]["database"] = "connected"
    except Exception as e:
        status["services"]["database"] = f"error: {str(e)}"
        status["status"] = "unhealthy"

    # 检查 Milvus
    try:
        from backend.milvus.client import get_milvus_client

        client = get_milvus_client()
        client.list_collections()
        status["services"]["milvus"] = "connected"
    except Exception as e:
        status["services"]["milvus"] = f"error: {str(e)}"
        status["status"] = "unhealthy"

    return status


# ==================== 启动入口 ====================


if __name__ == "__main__":
    import uvicorn

    print("\n启动 RAG Agent API 服务...")
    print("访问 http://localhost:8000/docs 查看 API 文档\n")

    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式自动重载
        log_level="info",
    )
