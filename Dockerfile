# 使用 Python 3.12 作为基础镜像
FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装 uv 包管理器
RUN pip install --no-cache-dir uv

# 复制项目文件
COPY pyproject.toml README.md uv.lock ./
COPY src/ ./src/

# 使用 uv 安装 Python 依赖
RUN uv sync --frozen


# 创建数据目录
RUN mkdir -p /app/data

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV WIKI_PATH=/app/data

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 健康检查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 启动命令
#ENTRYPOINT ["streamlit", "run", "src/nora_novel/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
ENTRYPOINT ["uv", "run", "streamlit", "run", "src/nora_novel/main.py", "--server.port=8501", "--server.address=0.0.0.0"]