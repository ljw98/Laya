# Laya Console

基于 [Laya](https://github.com/NandhaKishorM/laya)（非自回归 System 1 决策模型）的本地 Web 控制台：粘贴一段文本，提出一道类型化问题，一次前向得到答案与置信度。

- **仓库**：[ljw98/Laya](https://github.com/ljw98/Laya)
- **Docker 镜像名**：`heizicao/laya`（本地构建标签）
- **默认端口**：`8787`
- **模型权重**：不进 git，从 GitHub Releases 或 Hugging Face 下载

```text
.
├── index.html / app.css / app.js   # Web 界面
├── server.py                       # Flask API
├── download_models.py              # 模型下载（Release / HF）
├── Dockerfile / docker-compose.yml
├── requirements.txt
├── examples/demo_cli.py            # 命令行示例
├── logs/                           # 运行日志（gitignore）
├── releases/                       # 模型 zip 打包目录（gitignore）
└── laya-main/                      # Laya 源码与模型目录
    ├── laya/
    └── models/
        ├── laya/
        ├── laya-multilingual/
        └── laya-typed-decisions/
```

## 获取模型权重

### 方式一：GitHub Releases（推荐）

Release 中提供三个 zip：

| 文件 | 约大小 | 解压到 |
|---|---|---|
| `laya.zip` | 742 MB | `laya-main/models/laya/` |
| `laya-multilingual.zip` | 572 MB | `laya-main/models/laya-multilingual/` |
| `laya-typed-decisions.zip` | 742 MB | `laya-main/models/laya-typed-decisions/` |

下载地址：[Releases v1.0.0](https://github.com/ljw98/Laya/releases/tag/v1.0.0)

```powershell
python download_models.py --from-release --repo ljw98/Laya --tag v1.0.0
# 也可只下一个：
# python download_models.py --from-release --repo ljw98/Laya --tag v1.0.0 --only laya-multilingual
```

### 方式二：Hugging Face

```powershell
python download_models.py --hf-endpoint https://hf-mirror.com
```

## 快速开始

### Docker

```powershell
# 1. 准备权重（见上一节）
python download_models.py --from-release --repo ljw98/Laya --tag v1.0.0

# 2. 启动
docker-compose up -d --build

# 3. 浏览器打开
# http://127.0.0.1:8787
# 局域网 http://<本机IP>:8787
```

导出 / 导入镜像：

```powershell
docker save -o heizicao-laya-latest.tar heizicao/laya:latest
docker load -i heizicao-laya-latest.tar
```

### 本机 Python

```powershell
pip install -r requirements.txt
pip install -e ./laya-main

python download_models.py --from-release --repo ljw98/Laya --tag v1.0.0
python server.py
```

## 配置

| 环境变量 | 含义 | 默认 |
|---|---|---|
| `LAYA_HOST` / `LAYA_PORT` | 监听地址 | `0.0.0.0:8787` |
| `MODEL_DIR` | 权重根目录 | `./laya-main/models` |
| `LAYA_MODEL_MODE` | `local` 仅本地；`auto` 缺失时自动下载 | `local` |
| `HF_ENDPOINT` | Hugging Face 端点（可填镜像） | 官方源 |

权重目录结构（每个检查点需完整）：

```text
laya-main/models/<name>/
  rl_agent_config.json
  model.safetensors
  tokenizer/tokenizer.json
  tokenizer/tokenizer_config.json
  encoder/config.json
```

`<name>` 为 `laya`、`laya-multilingual` 或 `laya-typed-decisions`。

## Web 使用

1. 选择模型（单模型驻留，切换时自动加载 / 卸载）
2. 粘贴内容
3. 出一道题（`choice` / `score` / `noul`）
4. 开始分析

| 类型 | 输出 | 适用 |
|---|---|---|
| `choice` | 选项 + 概率 + 置信度 | 意图、部门、话题 |
| `score` | 期望档位 + 分布 | 紧急度、危害等级 |
| `noul` | P(成立) 0~1 | 是否退款、是否钓鱼 |

出题原则：多问「文本里写了什么」，少问「心里怎么想」。工单分诊、内容安全、提示护栏等任务更稳。

## HTTP API

### `GET /api/health`

```json
{ "ready": true, "resident": "multilingual", "model_mode": "local", "backend": "laya" }
```

### `GET /api/models`

返回检查点列表：是否本地完整、是否当前驻留。

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
| `questions.*.criteria` | choice：`{"标签": "说明"}`；score：数组从低到高；noul 可省略 |

## 模型对照

| API 参数 | 目录 | 特点 |
|---|---|---|
| `english` | `models/laya` | ModernBERT-large，英文最准 |
| `multilingual` | `models/laya-multilingual` | mmBERT，中文 / 多语更稳 |
| `typed` | `models/laya-typed-decisions` | typed-decisions 微调 |

中文内容建议默认 `multilingual`。

## 内存说明

- 采用**单模型驻留**，不会三个检查点同时加载。
- 加载 1 个检查点时进程 RSS 约 **1.8–2 GB**（fp32 权重 + PyTorch）。
- 切换模型会卸载上一个；Python 分配器可能仍保留数百 MB，属正常现象。

## 能力边界

- 冷门或主观题（情感变化、心理推断等）零样本可能接近随机；严肃业务请使用自有数据微调（见 `laya-main/notebooks/`）。
- 选项很多（约大于 50）时需调大 token 预算，或使用 `predict_shortlist`。
- 权重与 Laya 源码许可为 Apache 2.0（Convai Innovations）。

## 致谢

- 上游项目：[NandhaKishorM/laya](https://github.com/NandhaKishorM/laya)
- 本仓库提供 Web 控制台、Docker 镜像与模型分发打包。

## License

- Laya 源码与模型权重：Apache 2.0
- 本仓库 Web / API / Docker 配套代码：随仓库 License 说明
