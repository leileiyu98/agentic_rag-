"""Document loaders - 基于 LangChain 的文档加载封装

支持格式: txt, md, markdown, pdf, docx, doc, json, py, js, ts, html, css
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from langchain_core.documents import Document as LangChainDocument
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader


# 支持的文件扩展名
SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".pdf",
    ".docx",
    ".doc",
    ".json",
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
}


def load_document(file_path: Union[str, Path]) -> List[LangChainDocument]:
    """加载单个文档

    Args:
        file_path: 文件路径

    Returns:
        LangChain Document 列表 (PDF 可能返回多页)

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 不支持的文件格式
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"不支持的文件格式: {suffix}. 支持的格式: {SUPPORTED_EXTENSIONS}")

    # 根据扩展名选择 loader
    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    elif suffix in (".docx", ".doc"):
        loader = Docx2txtLoader(str(path))
    else:  # .txt, .md, .markdown, .py, .js, .ts, .html, .css, .json
        loader = TextLoader(str(path), encoding="utf-8")

    documents = loader.load()

    # 添加元数据
    for doc in documents:
        doc.metadata.update(_extract_metadata(path, suffix))

    return documents


def load_directory(
    directory: Union[str, Path],
    glob_pattern: str = "**/*",
    exclude_patterns: Optional[List[str]] = None,
    silent_errors: bool = True,
) -> List[LangChainDocument]:
    """批量加载目录中的文档

    Args:
        directory: 目录路径
        glob_pattern: 文件匹配模式
        exclude_patterns: 排除的模式列表
        silent_errors: 是否静默处理错误

    Returns:
        LangChain Document 列表
    """
    path = Path(directory)

    if not path.exists():
        raise FileNotFoundError(f"目录不存在: {directory}")
    if not path.is_dir():
        raise NotADirectoryError(f"不是目录: {directory}")

    documents = []
    exclude = exclude_patterns or ["__pycache__", ".git", ".env", "node_modules", ".venv", "venv"]

    for file_path in path.glob(glob_pattern):
        if file_path.is_dir():
            continue

        if any(pattern in str(file_path) for pattern in exclude):
            continue

        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            continue

        try:
            docs = load_document(file_path)
            documents.extend(docs)
        except Exception as e:
            if not silent_errors:
                print(f"加载文件失败 {file_path}: {e}")

    return documents


def _extract_metadata(path: Path, suffix: str) -> Dict[str, Any]:
    """提取文件元数据"""
    stat = path.stat()

    # 代码文件类型映射
    CODE_TYPES = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".html": "html",
        ".css": "css",
        ".json": "json",
    }

    if suffix in (".md", ".markdown"):
        doc_type = "markdown"
    elif suffix == ".pdf":
        doc_type = "pdf"
    elif suffix in (".docx", ".doc"):
        doc_type = "word"
    elif suffix in CODE_TYPES:
        doc_type = CODE_TYPES[suffix]
    else:
        doc_type = "text"

    return {
        "file_name": path.name,
        "file_path": str(path.absolute()),
        "file_size": stat.st_size,
        "file_extension": suffix,
        "modified_time": stat.st_mtime,
        "doc_type": doc_type,
    }


# 测试代码
if __name__ == "__main__":
    import json

    print("Document Loader 测试")
    print("=" * 50)
    print(f"支持的格式: {SUPPORTED_EXTENSIONS}")

    # 创建测试文件
    test_txt = "test_document.txt"
    if not os.path.exists(test_txt):
        print(f"\n创建测试文件: {test_txt}")
        with open(test_txt, "w", encoding="utf-8") as f:
            f.write("# 测试文档\n\n这是一个用于测试的文档。\n包含多行内容。")

    # 测试加载
    print(f"\n加载文本文件: {test_txt}")
    docs = load_document(test_txt)
    print(f"加载到 {len(docs)} 个文档")
    for i, doc in enumerate(docs):
        print(f"\n文档 {i + 1}:")
        print(f"  内容长度: {len(doc.page_content)} 字符")
        print(f"  元数据: {json.dumps(doc.metadata, indent=2, ensure_ascii=False)}")
