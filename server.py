"""Laya Console local API + static frontend.

Usage:
    python server.py

Environment:
    LAYA_HOST / LAYA_PORT     listen address (default 0.0.0.0:8787)
    MODEL_DIR                 checkpoint root (default ./laya-main/models)
    LAYA_MODEL_MODE           local | auto
                              local = only read MODEL_DIR (manual download)
                              auto  = download missing checkpoints on first use
    HF_ENDPOINT               optional Hugging Face endpoint
                              e.g. https://hf-mirror.com

Memory:
    只驻留当前选中的 1 个模型；切换时卸载上一个再加载新的，避免内存暴涨。
"""
from __future__ import annotations

import gc
import os
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent
MODEL_DIR = Path(os.environ.get("MODEL_DIR", ROOT / "laya-main" / "models"))
MODEL_MODE = (os.environ.get("LAYA_MODEL_MODE") or "local").strip().lower()
BUNDLE_REPO = os.environ.get("LAYA_HF_REPO", "convaiinnovations/laya")

MODELS = {
    "english": {
        "label": "laya",
        "name": "laya",
        "tag": "english",
        "desc": "英文基准版 · ModernBERT-large · 512 上下文 · 英文任务最准",
        "folder": "laya",
        "subfolder": None,
    },
    "multilingual": {
        "label": "laya-multilingual",
        "name": "laya-multilingual",
        "tag": "100+ langs",
        "desc": "多语言版 · mmBERT-base · 1024 上下文 · 中文/多语更稳，速度更快",
        "folder": "laya-multilingual",
        "subfolder": "multilingual",
    },
    "typed": {
        "label": "laya-typed-decisions",
        "name": "laya-typed-decisions",
        "tag": "finetuned",
        "desc": "决策微调版 · typed-decisions 业务题更对口 · 通用零样本偏弱",
        "folder": "laya-typed-decisions",
        "subfolder": "typed-decisions",
    },
}
DEFAULT_MODEL = "multilingual"

REQUIRED_FILES = (
    "rl_agent_config.json",
    "model.safetensors",
    "tokenizer/tokenizer.json",
    "tokenizer/tokenizer_config.json",
    "encoder/config.json",
)

app = Flask(__name__, static_folder=str(ROOT), static_url_path="")

# 仅驻留 1 个模型；用锁串行化加载/卸载，避免并行切换
_resident_key: str | None = None
_agent = None
_errors: dict[str, str] = {}
_load_lock = threading.Lock()


def model_path(key: str) -> Path:
    return MODEL_DIR / MODELS[key]["folder"]


def is_complete(path: Path) -> bool:
    return all((path / rel).is_file() and (path / rel).stat().st_size > 0 for rel in REQUIRED_FILES)


def ensure_local(key: str) -> Path:
    path = model_path(key)
    if is_complete(path):
        return path

    meta = MODELS[key]
    if MODEL_MODE != "auto":
        raise FileNotFoundError(
            f"模型不完整或不存在: {path}\n"
            f"  方式1 手动下载后放到该目录（需包含 {' / '.join(REQUIRED_FILES)}）\n"
            f"  方式2 设置 LAYA_MODEL_MODE=auto 自动下载\n"
            f"  可用 python download_models.py --only {meta['folder']}"
        )

    if os.environ.get("HF_ENDPOINT"):
        print(f"HF_ENDPOINT={os.environ['HF_ENDPOINT']}")
    print(f"auto-download {meta['folder']} -> {path}")
    path.mkdir(parents=True, exist_ok=True)
    from huggingface_hub import hf_hub_download

    prefix = f"{meta['subfolder']}/" if meta["subfolder"] else ""
    for rel in REQUIRED_FILES:
        target = path / rel
        if target.is_file() and target.stat().st_size > 0:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        hf_hub_download(
            repo_id=BUNDLE_REPO,
            filename=prefix + rel,
            local_dir=str(path),
        )
        nested = path / (prefix + rel)
        if nested != target and nested.exists():
            nested.replace(target)

    if not is_complete(path):
        raise RuntimeError(f"下载后仍不完整: {path}")
    return path


def unload_model() -> str | None:
    """释放当前驻留模型，返回被卸载的 key。"""
    global _resident_key, _agent
    old = _resident_key
    if _agent is not None or old is not None:
        _agent = None
        _resident_key = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:  # noqa: BLE001
            pass
        # Linux：把空闲堆还给操作系统，避免 RSS 只升不降
        try:
            import ctypes

            libc = ctypes.CDLL("libc.so.6")
            libc.malloc_trim(0)
        except Exception:  # noqa: BLE001
            pass
        print(f"unloaded model: {old}")
    return old


def load_model(key: str):
    """加载指定模型；若已有其他模型驻留则先卸载。单模型驻留，加载串行。"""
    global _resident_key, _agent
    if key not in MODELS:
        raise ValueError(f"unknown model: {key}")

    with _load_lock:
        if _resident_key == key and _agent is not None:
            return _agent

        prev = unload_model()
        if prev and prev != key:
            print(f"switch model: {prev} -> {key}")
        import laya

        path = ensure_local(key)
        t0 = time.perf_counter()
        _agent = laya.load(str(path), device="cpu")
        _resident_key = key
        _errors.pop(key, None)
        print(f"loaded {key} in {time.perf_counter() - t0:.1f}s")
        return _agent


def get_agent(key: str = DEFAULT_MODEL):
    key = key if key in MODELS else DEFAULT_MODEL
    return load_model(key)


@app.get("/")
def index():
    return send_from_directory(str(ROOT), "index.html")


@app.get("/api/models")
def list_models():
    items = []
    for key, meta in MODELS.items():
        path = model_path(key)
        items.append(
            {
                "id": key,
                "label": meta["label"],
                "name": meta.get("name", meta["label"]),
                "tag": meta.get("tag", ""),
                "desc": meta["desc"],
                "loaded": key == _resident_key,
                "local_complete": is_complete(path),
                "path": str(path),
                "error": _errors.get(key),
            }
        )
    return jsonify(
        {
            "default": DEFAULT_MODEL,
            "resident": _resident_key,
            "model_mode": MODEL_MODE,
            "hf_endpoint": os.environ.get("HF_ENDPOINT") or "https://huggingface.co",
            "model_dir": str(MODEL_DIR),
            "models": items,
        }
    )


@app.post("/api/model/select")
def select_model():
    """切换驻留模型：加载目标、卸载之前那个。并行请求会排队而不是报错。"""
    payload = request.get_json(force=True, silent=True) or {}
    key = payload.get("model") or DEFAULT_MODEL
    if key not in MODELS:
        return jsonify({"error": f"unknown model: {key}"}), 400
    try:
        t0 = time.perf_counter()
        load_model(key)
        return jsonify(
            {
                "resident": _resident_key,
                "label": MODELS[key].get("name", key),
                "switch_ms": (time.perf_counter() - t0) * 1000,
                "message": "ok",
            }
        )
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e), "model": key}), 500


@app.post("/api/model/unload")
def unload_api():
    old = unload_model()
    return jsonify({"unloaded": old, "resident": _resident_key})


@app.get("/api/health")
def health():
    return jsonify(
        {
            "ready": _agent is not None,
            "resident": _resident_key,
            "errors": _errors,
            "model_mode": MODEL_MODE,
            "backend": "laya",
        }
    )


@app.post("/api/predict")
def predict():
    payload = request.get_json(force=True, silent=True) or {}
    state = payload.get("state")
    questions = payload.get("questions")
    model_key = payload.get("model") or DEFAULT_MODEL

    if not isinstance(questions, dict) or not questions:
        return jsonify({"error": "questions must be a non-empty object"}), 400
    if state is None:
        return jsonify({"error": "state is required"}), 400
    if model_key not in MODELS:
        return jsonify({"error": f"unknown model: {model_key}"}), 400

    try:
        agent = get_agent(model_key)
        t0 = time.perf_counter()
        result = agent.predict(state, questions)
        ms = (time.perf_counter() - t0) * 1000
        out = {
            "answers": result.get("answers", result),
            "latency_ms": ms,
            "backend": "laya",
            "model": model_key,
            "model_label": MODELS[model_key].get("name", MODELS[model_key]["label"]),
            "resident": _resident_key,
        }
        if "routing" in result:
            out["routing"] = result["routing"]
        return jsonify(out)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": str(e), "model": model_key}), 500


if __name__ == "__main__":
    host = os.environ.get("LAYA_HOST", "0.0.0.0")
    port = int(os.environ.get("LAYA_PORT", "8787"))
    print(f"Laya Console  http://{host}:{port}")
    print(f"model dir    {MODEL_DIR}")
    print(f"model mode   {MODEL_MODE}")
    print(f"HF_ENDPOINT  {os.environ.get('HF_ENDPOINT') or '(default huggingface.co)'}")
    print("单模型驻留：切换时加载新模型并卸载旧模型（启动不预加载）")
    for key, meta in MODELS.items():
        path = model_path(key)
        flag = "ok" if is_complete(path) else "missing"
        print(f"  [{key}] {meta['folder']}  [{flag}]")
    app.run(host=host, port=port, debug=False)
