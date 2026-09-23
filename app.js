/* Laya 一题决策 — 单题模块，三种题型 + 三种模型 */

const HINTS = {
  choice: "选项题：每行一个选项，模型从中选一个",
  score: "打分题：每行一个档位，从低到高",
  noul: "是非题：只写问题，输出成立概率",
};

const PLACEHOLDERS = {
  choice: "要问什么？例如：客户想要什么？",
  score: "要问什么？例如：有多紧急？",
  noul: "要问什么？例如：是否明确要求退款？",
};

const DEFAULTS = {
  choice: {
    ins: "客户想要什么？",
    crit: "退款\n技术支持\n账单咨询\n咨询信息\n取消订阅\n其他",
  },
  score: {
    ins: "有多紧急？",
    crit: "不紧急\n尽快处理\n阻塞或硬截止",
  },
  noul: {
    ins: "是否明确要求退款？",
    crit: "",
  },
};

const MODEL_FALLBACK = {
  english: {
    name: "laya",
    tag: "english",
    desc: "英文基准版 · ModernBERT-large · 512 上下文 · 英文任务最准",
  },
  multilingual: {
    name: "laya-multilingual",
    tag: "100+ langs",
    desc: "多语言版 · mmBERT-base · 1024 上下文 · 中文/多语更稳，速度更快",
  },
  typed: {
    name: "laya-typed-decisions",
    tag: "finetuned",
    desc: "决策微调版 · typed-decisions 业务题更对口 · 通用零样本偏弱",
  },
};

let qType = "choice";
let modelKey = "multilingual";
let apiLive = false;

const $ = (sel) => document.querySelector(sel);

function setConn(live, resident) {
  apiLive = live;
  const pill = $("#conn-pill");
  if (!live) {
    pill.textContent = "演示模式";
    pill.className = "pill demo";
    return;
  }
  if (resident) {
    pill.textContent = "已加载 " + resident;
    pill.className = "pill live";
  } else {
    pill.textContent = "已连接 · 未加载模型";
    pill.className = "pill";
  }
}

async function ping() {
  try {
    const r = await fetch("/api/health");
    if (!r.ok) throw new Error("bad");
    const j = await r.json();
    setConn(true, j.resident || null);
  } catch {
    setConn(false);
  }
}

async function loadModels() {
  try {
    const r = await fetch("/api/models");
    if (!r.ok) return;
    const data = await r.json();
    const map = {};
    (data.models || []).forEach((m) => {
      map[m.id] = m;
    });
    document.querySelectorAll("#model-seg .seg-btn").forEach((btn) => {
      const id = btn.dataset.model;
      const meta = map[id] || MODEL_FALLBACK[id];
      if (meta && meta.name) {
        btn.querySelector(".m-name").textContent = meta.name;
      }
      if (meta && meta.tag) {
        btn.querySelector(".m-tag").textContent = meta.tag;
      }
      if (meta && meta.error) {
        btn.title = meta.error;
        btn.classList.add("error");
      }
    });
    updateModelHint();
  } catch {
    /* 演示模式忽略 */
  }
}

function updateModelHint() {
  const meta = MODEL_FALLBACK[modelKey];
  $("#model-hint").textContent = `当前：${meta.desc}`;
}

function pct(x) {
  return (Number(x) * 100).toFixed(0) + "%";
}

function parseLines(raw) {
  return String(raw || "")
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
}

function setType(type) {
  qType = type;
  document.querySelectorAll("#type-seg .seg-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.type === type);
  });

  const crit = $("#q-crit");
  const ins = $("#q-ins");
  ins.placeholder = PLACEHOLDERS[type];
  $("#crit-hint").textContent = HINTS[type];

  if (type === "noul") {
    crit.disabled = true;
    crit.value = "";
    crit.placeholder = "是非题无需选项";
  } else {
    crit.disabled = false;
    crit.placeholder =
      type === "choice" ? "每行一个选项，例如：退款" : "每行一个档位，从低到高，例如：不紧急";
  }
  updateRequestSnippet();
}

function fillDefault(type) {
  const d = DEFAULTS[type];
  $("#q-ins").value = d.ins;
  if (type !== "noul") $("#q-crit").value = d.crit;
  else $("#q-crit").value = "";
  updateRequestSnippet();
}

function currentQuestion() {
  const instructions = $("#q-ins").value.trim() || "请判断";
  const lines = parseLines($("#q-crit").value);
  if (qType === "choice") {
    const criteria = {};
    lines.forEach((l) => (criteria[l] = null));
    if (!Object.keys(criteria).length) criteria["是"] = null;
    return { type: "choice", instructions, criteria };
  }
  if (qType === "score") {
    return {
      type: "score",
      instructions,
      criteria: lines.length ? lines : ["低", "中", "高"],
    };
  }
  return { type: "noul", instructions };
}

function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function updateRequestSnippet() {
  const bodyEl = $("#req-body");
  if (!bodyEl) return;
  const text = $("#state-text").value.trim();
  const question = currentQuestion();
  bodyEl.textContent = JSON.stringify(
    {
      model: modelKey,
      state: { text },
      questions: { q1: question },
    },
    null,
    2
  );
}

function barRow(name, p, top) {
  const w = (Math.max(0, Math.min(1, Number(p))) * 100).toFixed(1) + "%";
  return `
    <div class="bar-row">
      <div class="name">${escapeHtml(name)}</div>
      <div class="track"><div class="fill ${top ? "top" : ""}" data-w="${w}"></div></div>
      <div class="pct">${pct(p)}</div>
    </div>`;
}

function demoAnswer(question) {
  if (question.type === "choice") {
    const labels = Object.keys(question.criteria);
    const probs = {};
    labels.forEach((l, i) => {
      probs[l] = i === 0 ? 0.7 : 0.3 / Math.max(1, labels.length - 1);
    });
    return { type: "choice", choice: labels[0], probabilities: probs, confidence: 0.7 };
  }
  if (question.type === "score") {
    const levels = question.criteria;
    const probs = {};
    levels.forEach((_, i) => {
      probs[i] = i === levels.length - 1 ? 0.55 : 0.45 / levels.length;
    });
    const legend = {};
    levels.forEach((l, i) => (legend[i] = l));
    return {
      type: "score",
      score: Math.max(0, levels.length - 1.3),
      legend,
      probabilities: probs,
      confidence: 0.3,
    };
  }
  return { type: "noul", noul: 0.66, confidence: 0.66 };
}

function renderResult(question, ans, elapsedMs, modelLabel) {
  const box = $("#result");
  const gate = 0.85;
  const conf = ans.confidence ?? 0;
  const auto = conf >= gate;
  const type = ans.type || question.type;
  const title = question.instructions;
  const typeLabel = type === "choice" ? "选项" : type === "score" ? "打分" : "是非";

  let main = "";
  let sub = "";
  let bars = "";

  if (type === "choice") {
    const probs = Object.entries(ans.probabilities || {}).sort((a, b) => b[1] - a[1]);
    main = ans.choice;
    sub = `置信度 ${pct(conf)}`;
    bars = probs.map(([n, p], i) => barRow(n, p, i === 0)).join("");
  } else if (type === "score") {
    const legend = ans.legend || {};
    const probs = ans.probabilities || {};
    const keys = Object.keys(probs).sort((a, b) => Number(a) - Number(b));
    const top = keys.reduce((a, b) => (Number(probs[a]) >= Number(probs[b]) ? a : b), keys[0]);
    main = legend[top] ?? `档位 ${top}`;
    sub = `得分 ${Number(ans.score).toFixed(1)} · 置信度 ${pct(conf)}`;
    bars = keys.map((k) => barRow(legend[k] ?? k, probs[k], k === top)).join("");
  } else {
    const p = ans.noul ?? 0;
    main = p >= 0.5 ? "是" : "否";
    sub = `P(成立) ${pct(p)} · 置信度 ${pct(conf)}`;
    bars = barRow("是", p, p >= 0.5) + barRow("否", 1 - p, p < 0.5);
  }

  box.innerHTML = `
    <article class="result-card">
      <p class="q-title">${escapeHtml(title)} · ${typeLabel} · ${escapeHtml(modelLabel || "")}</p>
      <div class="answer-main">${escapeHtml(String(main))}</div>
      <div class="answer-sub">${sub}</div>
      <div class="meta-row">
        <span class="chipy ${auto ? "auto" : "human"}">${auto ? "自动执行" : "人工复核"}</span>
        <span class="chipy">${elapsedMs.toFixed(0)} ms</span>
      </div>
      <div class="bars">${bars}</div>
    </article>
  `;
  box.classList.remove("hidden");
  $("#empty").classList.add("hidden");

  requestAnimationFrame(() => {
    box.querySelectorAll(".fill").forEach((el) => {
      el.style.width = el.dataset.w;
    });
  });
}

async function run() {
  const btn = $("#run");
  const text = $("#state-text").value.trim();
  if (!text) {
    alert("请先粘贴一段内容");
    return;
  }
  const question = currentQuestion();
  const questions = { q1: question };
  const modelLabel = (MODEL_FALLBACK[modelKey] || {}).name || modelKey;

  btn.disabled = true;
  btn.textContent = "分析中…";
  const t0 = performance.now();

  try {
    if (apiLive) {
      const r = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: { text }, questions, model: modelKey }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.error || r.statusText);
      }
      const data = await r.json();
      const ans = (data.answers && data.answers.q1) || {};
      renderResult(question, ans, performance.now() - t0, data.model_label || modelLabel);
      ping();
    } else {
      await new Promise((r) => setTimeout(r, 300));
      renderResult(question, demoAnswer(question), performance.now() - t0, modelLabel);
    }
  } catch (e) {
    alert("分析失败：" + e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "3 · 开始分析";
  }
}

function bind() {
  document.querySelectorAll("#type-seg .seg-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      setType(btn.dataset.type);
      fillDefault(btn.dataset.type);
    });
  });

  document.querySelectorAll("#model-seg .seg-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (btn.disabled) return;
      document.querySelectorAll("#model-seg .seg-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      modelKey = btn.dataset.model;
      updateModelHint();
      updateRequestSnippet();
      // 切换时加载新模型并卸载上一个；期间禁用模型与分析按钮，避免重入
      if (apiLive) {
        const segs = [...document.querySelectorAll("#model-seg .seg-btn")];
        const runBtn = $("#run");
        segs.forEach((b) => (b.disabled = true));
        runBtn.disabled = true;
        const prevText = runBtn.textContent;
        runBtn.textContent = "切换模型中…";
        try {
          await fetch("/api/model/select", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ model: modelKey }),
          });
          ping();
        } catch {
          /* 预测时仍会按需加载 */
        } finally {
          segs.forEach((b) => (b.disabled = false));
          runBtn.disabled = false;
          runBtn.textContent = prevText;
        }
      }
    });
  });

  $("#run").addEventListener("click", run);
  ["#state-text", "#q-ins", "#q-crit"].forEach((sel) => {
    $(sel).addEventListener("input", updateRequestSnippet);
  });

  const copyBtn = $("#copy-req");
  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(
          "POST http://127.0.0.1:8787/api/predict\n" +
            "Content-Type: application/json\n\n" +
            $("#req-body").textContent
        );
        copyBtn.textContent = "已复制";
        setTimeout(() => (copyBtn.textContent = "复制"), 1200);
      } catch {
        /* ignore */
      }
    });
  }
}

bind();
setType("choice");
updateModelHint();
updateRequestSnippet();
loadModels();
ping();
setInterval(ping, 8000);
