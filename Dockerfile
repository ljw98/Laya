# Laya Console — CPU 推理镜像（不含模型权重）
# 权重：挂载到 /app/laya-main/models，或启动时按 LAYA_MODEL_MODE 自动下载
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    LAYA_HOST=0.0.0.0 \
    LAYA_PORT=8787 \
    PYTHONPATH=/app \
    MODEL_DIR=/app/laya-main/models \
    LAYA_MODEL_MODE=local

WORKDIR /app

# CPU 版 PyTorch（transformers 5.x 需要 >= 2.5）
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1+cpu

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY laya-main/laya /app/laya
COPY server.py download_models.py index.html app.css app.js /app/

RUN mkdir -p /app/laya-main/models /app/logs

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/api/health', timeout=3)"

CMD ["python", "server.py"]
