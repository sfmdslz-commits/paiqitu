# 演员排期表生成器 - 容器部署
# 基于 Playwright 官方镜像（已内置 Chromium 与运行依赖），只需补装中文字体。
FROM mcr.microsoft.com/playwright/python:v1.58.0-noble

# 避免容器内生成 pyc，关闭 Flask 调试
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    FLASK_APP=app.py

WORKDIR /app

# 中文字体：思源宋体（Noto Serif CJK）与思源黑体（Noto Sans CJK），均为 OFL 商用授权
RUN apt-get update && apt-get install -y --no-install-recommends \
        fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 业务代码
COPY app.py generator.py ./
COPY templates ./templates

# 运行时目录（生成图片与上传底图）
RUN mkdir -p outputs uploads

EXPOSE 8080

# gunicorn 单 worker + 多线程：渲染用全局锁串行，避免多进程重复占用 Chromium 内存
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 180 app:app"]
