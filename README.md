# jev / heizicao-laya

基于 [Laya](https://github.com/NandhaKishorM/laya)（非自回归 System 1 决策模型）的本地 Web 控制台：贴一段文本，出一道类型化问题，一次前向得到答案与置信度。

- 镜像名：`heizicao/laya`
- 默认端口：`8787`
- 代码在仓库；**模型 zip 放在 GitHub Releases**（单文件远超 100MB，不能进 git）

```text
jev/
├── index.html / app.css / app.js   # Web 界面
├── server.py                       # Flask API
├── download_models.py              # HF 或 GitHub Releases 下载
├── Dockerfile / docker-compose.yml
├── requirements.txt
├── examples/demo_cli.py
├── logs/                           # gitignore
├── releases/                       # 本地打包 zip（gitignore），用于传 Release
└── laya-main/                      # Laya 源码 + models/
    ├── laya/
    └── models/
        ├── laya/
        ├── laya-multilingual/
        └── laya-typed-decisions/
```

## 获取模型权重

### 方式 1：GitHub Releases（给用户直接下）

本仓库 `releases/` 已打好三个 zip（打包机本地）：

| 文件 | 约大小 |
|---|---|
| `releases/laya.zip` | 742 MB |
| `releases/laya-multilingual.zip` | 572 MB |
| `releases/laya-typed-decisions.zip` | 742 MB |

上传到 GitHub Release（示例 tag `v1.0.0`，仓库名以你实际为准）：

```powershell
# 网页：Releases → Draft → 上传上述三个 zip
# 或 gh（需已登录）：
gh release create v1.0.0 `
  releases/laya.zip `
  releases/laya-multilingual.zip `
  releases/laya-typed-decisions.zip `
  --title "Laya model weights" `
  --notes "Checkpoints for heizicao/laya console"
```

用户下载（解压到 `laya-main/models/<对应名字>/`）：

```powershell
python download_models.py --from-release --repo heizicao/laya --tag v1.0.0
# 或手动：
# 解压 laya.zip            -> laya-main/models/laya/
# 解压 laya-multilingual.zip -> laya-main/models/laya-multilingual/
# 解压 laya-typed-decisions.zip -> laya-main/models/laya-typed-decisions/
```

### 方式 2：Hugging Face

```powershell
python download_models.py --hf-endpoint https://hf-mirror.com
```

## 快速开始

### Docker

```powershell
# 1) 准备权重（任选一种）
python download_models.py --from-release --repo <你的仓库> --tag v1.0.0
python download_models.py --hf-endpoint https://hf-mirror.com
# 或 $env:LAYA_MODEL_MODE="auto"

# 2) 启动
docker-compose up -d --build

# 3) 打开
# http://127.0.0.1:8787
```

导出镜像：

```powershell
docker save -o heizicao-laya-latest.tar heizicao/laya:latest
docker load -i heizicao-laya-latest.tar
```

### 本机 Python

```powershell
pip install -r requirements.txt
pip install -e ./laya-main
python download_models.py --from-release --repo <你的仓库> --tag v1.0.0
python server.py
```

## 配置

| 环境变量 | 含义 | 默认 |
|---|---|---|
| `LAYA_HOST` / `LAYA_PORT` | 监听地址 | `0.0.0.0:8787` |
| `MODEL_DIR` | 权重根目录 | `./laya-main/models` |
| `LAYA_MODEL_MODE` | `local` 仅本地 / `auto` 缺失自动下载 | `local` |
| `HF_ENDPOINT` | Hugging Face 端点（可填镜像） | 官方 |

权重目录结构（每个检查点需完整）：

```text
laya-main/models/<name>/
  rl_agent_config.json
  model.safetensors
  tokenizer/tokenizer.json
  tokenizer/tokenizer_config.json
  encoder/config.json
```

`<name>` ∈ `laya` | `laya-multilingual` | `laya-typed-decisions`。

## Web 用法

1. 选择模型（单模型驻留，切换时加载/卸载）
2. 粘贴内容
3. 出一道题（`choice` / `score` / `noul`）
4. 开始分析

| type | 输出 | 适合 |
|---|---|---|
| `choice` | 选项 + 概率 + 置信度 | 意图、部门、话题 |
| `score` | 期望档位 + 分布 | 紧急度、危害等级 |
| `noul` | P(成立) 0~1 | 是否退款、是否钓鱼 |

出题原则：问「文本里写了什么」，少问「心里怎么想」。工单分诊、内容安全、提示护栏更稳。

## HTTP API

### `GET /api/health`

```json
{ "ready": true, "resident": "multilingual", "model_mode": "local", "backend": "laya" }
```

### `GET /api/models`

检查点列表（是否本地完整、是否当前驻留）。

### `POST /api/model/select`

```json
{ "model": "english" | "multilingual" | "typed" }
```

加载目标模型并卸载上一个（单模型驻留）。

### `POST /api/model/unload`

卸载当前驻留模型。

### `POST /api/predict`

```json
{
  "model": "multilingual",
  "state": { "text": "请今天退款，否则取消订阅。" },
  "questions": {
    "q1": {
      "type": "choice",
      "instructions": "客户想要什么？",
      "criteria": { "退款": null, "技术支持": null, "其他": null }
    }
  }
}
```

| 字段 | 说明 |
|---|---|
| `model` | `english` \| `multilingual` \| `typed` |
| `state` | 对象或字符串 |
| `questions.*.type` | `choice` \| `score` \| `noul` |
| `questions.*.instructions` | 问题文本 |
| `questions.*.criteria` | choice：`{"标签": "说明"}`；score：数组低→高；noul 可省略 |

## 模型对照

| API | 目录 | 特点 |
|---|---|---|
| `english` | `models/laya` | ModernBERT-large，英文最准 |
| `multilingual` | `models/laya-multilingual` | mmBERT，中文/多语更稳 |
| `typed` | `models/laya-typed-decisions` | typed-decisions 微调 |

中文建议默认 `multilingual`。

## 内存说明

- **单模型驻留**，不会三个一起加载。
- 加载 1 个检查点时进程 RSS 大约 **1.8–2GB**（fp32 权重 + PyTorch）。
- 切换模型会卸载上一个；Python 分配器可能仍保留数百 MB，属正常。

## 能力边界

- 冷门/主观题（情感变化、心理推断）零样本可能接近随机；严肃业务请微调（见 `laya-main/notebooks/`）。
- 选项很多（约 >50）时需调大 token 预算或 `predict_shortlist`。
- 权重许可见 Laya 上游（Apache 2.0）。

## 上传 GitHub 时注意

- **不要提交** `laya-main/models/**/model.safetensors`、`*.tar`、`logs/`（已在 `.gitignore`）。
- 仓库保持代码 + 文档即可；用户用 `download_models.py` 或 `LAYA_MODEL_MODE=auto` 取权重。
- `laya-main/` 为 Laya 源码（Apache 2.0），上游：https://github.com/NandhaKishorM/laya

## License

- 本项目 Web/API 壳：随仓库约定
- Laya 源码与权重：Apache 2.0（Convai Innovations）
