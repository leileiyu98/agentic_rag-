#!/usr/bin/env python3
"""
RAG Agent API 启动脚本

使用方法:
    python run_api.py

    # 或指定参数
    python run_api.py --host 0.0.0.0 --port 8080 --reload
"""

import argparse
import uvicorn
import os
import sys

# 添加项目根目录到 Python 路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

# 加载 .env 文件
from dotenv import load_dotenv

load_dotenv()


def check_environment():
    """检查环境配置"""
    print("=" * 60)
    print("环境检查")
    print("=" * 60)

    # 检查 .env 文件
    if not os.path.exists(".env"):
        print("[!] 警告: .env 文件不存在，将使用系统环境变量")
        print("  建议: cp .env.example .env 并填写配置")
    else:
        print("[OK] .env 文件存在")

    # 检查 OPENAI_API_KEY
    if not os.getenv("OPENAI_API_KEY"):
        print("[X] 错误: OPENAI_API_KEY 环境变量未设置")
        print("  请在 .env 文件中设置 OPENAI_API_KEY")
        return False
    else:
        print("[OK] OPENAI_API_KEY 已配置")

    print()
    return True


def main():
    parser = argparse.ArgumentParser(
        description="启动 RAG Agent API 服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_api.py                    # 默认启动
  python run_api.py --reload           # 开发模式（自动重载）
  python run_api.py --port 8080        # 指定端口
  python run_api.py --host 0.0.0.0     # 允许外部访问
        """,
    )

    parser.add_argument(
        "--host", default="0.0.0.0", help="监听主机地址 (默认: 0.0.0.0)"
    )
    parser.add_argument("--port", type=int, default=8000, help="监听端口 (默认: 8000)")
    parser.add_argument(
        "--reload", action="store_true", help="开发模式：代码变更时自动重载"
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="工作进程数 (默认: 1，生产环境建议增加)"
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="日志级别 (默认: info)",
    )

    args = parser.parse_args()

    # 检查环境
    if not check_environment():
        sys.exit(1)

    print("=" * 60)
    print("启动 RAG Agent API 服务")
    print("=" * 60)
    print(f"主机: {args.host}")
    print(f"端口: {args.port}")
    print(f"重载: {'是' if args.reload else '否'}")
    print(f"工作进程: {args.workers}")
    print(f"日志级别: {args.log_level}")
    print("=" * 60)
    print(f"API 文档: http://{args.host}:{args.port}/docs")
    print(f"健康检查: http://{args.host}:{args.port}/health")
    print("=" * 60)
    print()

    # 启动服务
    uvicorn.run(
        "backend.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
