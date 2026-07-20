<script setup>
// ============================================================
// 智貸先鋒 企業授信情資服務網 — Vue 3 版(政府服務網站設計語言)
// 參考:data.taipei / schema.gov.tw / ey.gov.tw 等台灣政府入口網
// 設計原則:白底、單一機關色(深藍 sky-900)、小圓角、1px 細框、
//          左側色條區塊標題、列表導向、制式 footer、字級調整
// ※ 規格書 v1.0 §3.1 原定 React;改用 Vue 需提契約變更(v1.1)並公告全員
// ※ 雷達圖由 recharts(React 專用)改為手刻 SVG,互動行為不變
// 接真實 API:搜尋 [API] 標記處
// ============================================================
import { ref, reactive, computed, nextTick } from "vue";

const focusRing = "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-700 focus-visible:ring-offset-1";
const num = "tabular-nums";

// 三個 Agent 的識別(政府風:白卡 + 左側色條,不用大面積色塊)
// 7.2:finance #D97706 amber / tech #0891B2 cyan / judge #E11D48 rose
const AGENT = {
  finance: { name: "財務分析", edge: "border-l-amber-500", text: "text-amber-800", chip: "bg-amber-50 text-amber-800 border-amber-300" },
  tech: { name: "技術情報", edge: "border-l-cyan-600", text: "text-cyan-800", chip: "bg-cyan-50 text-cyan-800 border-cyan-300" },
  judge: { name: "風險審查", edge: "border-l-rose-600", text: "text-rose-800", chip: "bg-rose-50 text-rose-800 border-rose-300" },
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ============================================================
// [API] 呼叫層(規格書 5.1 / 5.2 / 7.3)
// USE_MOCK=true:開發與 Demo 保險絲,回傳內建範例 JSON
// 整合日:改為 false,並以環境變數 VITE_API_BASE 指向後端
// ============================================================
const USE_MOCK = true;
const API_BASE =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE) || "http://localhost:8000";

async function callApi(path, body) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 90_000); // 前端逾時 90 秒(5.1)
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      // 統一錯誤格式(5.2):非 200 一律解析 error.code / error.message
      throw {
        code: data?.error?.code || "INTERNAL_ERROR",
        message: data?.error?.message || "系統發生未預期錯誤,請重試。",
      };
    }
    return data;
  } catch (e) {
    if (e?.name === "AbortError") throw { code: "EAP_TIMEOUT", message: "系統回應逾時,請重試。" };
    if (e?.code) throw e;
    throw { code: "INTERNAL_ERROR", message: "無法連線至後端服務,請確認網路後重試。" };
  } finally {
    clearTimeout(timer);
  }
}

// Mock 模式與真實 API 的統一入口:整合日不需改動其他程式
async function reviewApi(path, body, mock, mockDelay = 1800) {
  if (USE_MOCK) { await sleep(mockDelay); return mock; }
  return callApi(path, body);
}

// ============================================================
// Mock 資料([API] 全部可由後端取代)
// ============================================================
const CASES = [
  { id: "12345678", name: "XX 固態電池科技股份有限公司", industry: "儲能/電池", stage: "post", score: 68, updated: "115-07-16", status: "審查中" },
  { id: "23456789", name: "OO 低軌衛星通訊股份有限公司", industry: "太空科技", stage: "pre", score: null, updated: "115-07-15", status: "情資蒐集" },
  { id: "34567890", name: "ΔΔ 基因定序服務股份有限公司", industry: "生技醫療", stage: "mid", score: 74, updated: "115-07-14", status: "面談排程" },
];

// 以下三筆結構 = 規格書第 5 章範例回應 JSON,欄位名一律 snake_case(7.1)
const MOCK = {
  finance: { agent: "finance", score: 58, findings: [ // AgentResult(6.1)
    { text: "近三年資本支出年增 82%,自由現金流連續兩年為負,擴產資金高度依賴外部融資。", cite: "113 年度財報 p.45", confidence: 0.92 },
    { text: "流動比率 0.94,低於同業中位數 1.6,短期償債能力偏弱。", cite: "TWSE 財報摘要 API", confidence: 0.88 },
  ]},
  tech: { agent: "tech", score: 81, findings: [ // AgentResult(6.1)
    { text: "固態電解質相關專利 47 件,12 件被國際大廠引用,技術護城河明確。", cite: "TIPO 專利檢索", confidence: 0.95 },
    { text: "研報預估固態電池 2028 市場 CAGR 34%,惟量產良率仍在爬坡。", cite: "產業研究報告 2025Q4", confidence: 0.74 },
  ]},
  judge: { // JudgeResult(6.3)
    agent: "judge",
    contradictions: [
      { title: "量產時程 vs 資金缺口", detail: "技術面預估 2027 量產放量,但財務面現金流為負、流動比率僅 0.94,資金銜接方案未被說明,列為面談必問。", severity: "high" },
      { title: "客戶集中風險未被技術面納入", detail: "前兩大客戶佔營收 61%,若即為專利引用大廠,技術授權與訂單高度綁定,風險應合併評估。", severity: "medium" },
    ],
    verdict: "技術護城河成立(採信);財務體質偏弱(採信);市場預估缺客戶結構佐證(部分採信)。綜合 71 分,建議附條件核貸並於面談釐清資金方案。",
    final_score: 71,
    waterfall: [
      { label: "基礎分", value: 60, type: "base" }, { label: "技術護城河", value: 18, type: "plus" },
      { label: "產業景氣", value: 9, type: "plus" }, { label: "財務體質", value: -12, type: "minus" },
      { label: "客戶集中", value: -4, type: "minus" },
    ],
  },
  radar: [
    { key: "tech", label: "技術壁壘", score: 82, benchmark: 55, agent: "tech", reason: "專利 47 件、12 件遭國際大廠引用,近三年申請量成長 3 倍。", cites: ["TIPO 專利檢索"] },
    { key: "market", label: "市場規模", score: 74, benchmark: 60, agent: "tech", reason: "2028 CAGR 預估 34%,惟量產良率爬坡中,放量時點不確定。", cites: ["產業研報 2025Q4"] },
    { key: "finance", label: "財務體質", score: 48, benchmark: 65, agent: "finance", reason: "自由現金流連兩年為負、流動比率 0.94,為六維最弱項。", cites: ["113 年報 p.45"] },
    { key: "legal", label: "訴訟風險", score: 71, benchmark: 70, agent: "judge", reason: "近五年僅一件勞資調解已和解,無專利侵權訴訟在案。", cites: ["司法院裁判書 API"] },
    { key: "esg", label: "ESG 合規", score: 66, benchmark: 68, agent: "judge", reason: "一筆廢水裁罰(12 萬)已改善結案,勞動部名單無紀錄。", cites: ["環境部裁罰紀錄"] },
    { key: "macro", label: "產業景氣", score: 77, benchmark: 62, agent: "finance", reason: "EV 滲透率上升、鋰價回落 40%,循環位置有利。", cites: ["FRED 指數"] },
  ],
  questions: [
    { id: 1, dim: "財務體質", q: "自由現金流連續兩年為負,量產前 2–3 年資金缺口的具體銜接方案?", why: "財務分析 Agent 判定最大違約風險(113 年報 p.45)" },
    { id: 2, dim: "市場規模", q: "目前量產良率實際數字?損益兩平所需良率門檻?", why: "技術情報 Agent 發現新聞提及良率仍在爬坡(GDELT)" },
    { id: 3, dim: "技術壁壘", q: "前兩大客戶是否即為專利主要引用方?合約年限?", why: "審查官交叉質詢發現客戶集中與技術授權可能綁定" },
  ],
  postExtract: {
    commitments: [
      { item: "提供 B 輪投資意向書副本", owner: "財務長 林OO", due: "115-08-15" },
      { item: "提供良率改善合約", owner: "技術長 張OO", due: "115-08-15" },
    ],
    responses: [
      { risk: "資金銜接方案", summary: "B 輪意向書 8 億、Q4 交割,惟未具約束力", verdict: "partial" },
      { risk: "量產良率門檻", summary: "現況 63%/門檻 75%,有改善合約與明確時程", verdict: "resolved" },
      { risk: "客戶集中與專利綁定", summary: "證實綁定、2027 到期,續約中且第三客戶送樣", verdict: "partial" },
    ],
    newRisks: [{ text: "廠房二期再投入 12 億,原財報未揭露,資金缺口實際擴大。" }],
  },
  postScore: {
    final: 68,
    waterfall: [
      { label: "拜訪前基準", value: 71, type: "base" }, { label: "良率已化解", value: 8, type: "plus" },
      { label: "承諾具體可驗", value: 4, type: "plus" }, { label: "資金仍未落定", value: -6, type: "minus" },
      { label: "未揭露支出", value: -9, type: "minus" }, // 6.5:label 6 字以內
    ],
    rec: "附條件核貸:以 8/15 承諾文件到齊 + B 輪正式簽約為撥款前提;二期廠房資金計畫須補件。",
  },
};

const VERDICT = {
  resolved: { label: "已化解", cls: "bg-emerald-50 text-emerald-800 border-emerald-400" },
  partial: { label: "部分化解", cls: "bg-amber-50 text-amber-800 border-amber-400" },
  unresolved: { label: "未化解", cls: "bg-rose-50 text-rose-800 border-rose-400" },
};
const STAGE_LABEL = { pre: "拜訪前", mid: "拜訪中", post: "拜訪後" };

// 矛盾嚴重度(6.4):severity 決定警示框顏色深淺
const SEVERITY = {
  high:   { label: "高", box: "border-rose-400 bg-rose-100",  chip: "bg-rose-600 text-white border-rose-600" },
  medium: { label: "中", box: "border-rose-300 bg-rose-50",   chip: "bg-rose-50 text-rose-800 border-rose-400" },
  low:    { label: "低", box: "border-rose-200 bg-white",     chip: "bg-white text-rose-700 border-rose-300" },
};

const TABS = [
  { key: "committee", label: "AI 審查會議" },
  { key: "pre", label: "拜訪前情資" },
  { key: "mid", label: "拜訪中提詞" },
  { key: "post", label: "拜訪後評分" },
];

// ============================================================
// 全域版面狀態
// ============================================================
const page = ref("dashboard");
const current = ref(null);
const query = ref("");
const nav = ref("案件總覽");
const fontScale = ref("m");
const fontSize = computed(() => ({ s: "15px", m: "16px", l: "17.5px" }[fontScale.value]));
const fontSizes = [{ k: "s", label: "小" }, { k: "m", label: "中" }, { k: "l", label: "大" }];
const navItems = ["案件總覽", "情資查詢", "報告中心", "關於平臺"];

function goHome() { page.value = "dashboard"; current.value = null; nav.value = "案件總覽"; }
function onNav(t) { nav.value = t; if (t === "案件總覽") goHome(); }
function openCase(c) { current.value = c; page.value = "case"; tab.value = "committee"; }

const caseList = computed(() => {
  const q = query.value.trim();
  return CASES.filter((c) => !q || c.name.includes(q) || c.id.includes(q));
});
const announcements = [
  ["115-07-16", "系統更新", "AI 審查委員會新增「交叉質詢」逐字揭露功能。"],
  ["115-07-14", "資料介接", "已完成司法院裁判書開放 API 之訴訟風險訊號介接。"],
  ["115-07-10", "功能上線", "拜訪中「即時提詞卡」行動版正式提供試用。"],
];

// ============================================================
// 頁籤 1:AI 審查會議(phase 狀態機 7.1:idle/finance/tech/judge/done)
// ============================================================
const tab = ref("committee");
const phase = ref("idle");
const r = reactive({ finance: null, tech: null, judge: null });
const err = ref(null);
const committeeEnd = ref(null);
const busy = computed(() => phase.value !== "idle" && phase.value !== "done");

function scrollCommittee() { nextTick(() => committeeEnd.value?.scrollIntoView({ behavior: "smooth", block: "nearest" })); }

// resume:7.3 已渲染卡片保留,重試從失敗的那一段開始
async function runCommittee(resume = false) {
  err.value = null;
  const c = current.value;
  const req = { company_id: c.id, company_name: c.name }; // 5.3 Request
  if (!resume) { r.finance = null; r.tech = null; r.judge = null; }
  try {
    if (!r.finance) {
      phase.value = "finance"; scrollCommittee();
      r.finance = await reviewApi("/api/review/finance", req, MOCK.finance);   // 5.3
    }
    if (!r.tech) {
      phase.value = "tech"; scrollCommittee();
      r.tech = await reviewApi("/api/review/tech", req, MOCK.tech);            // 5.4
    }
    phase.value = "judge"; scrollCommittee();
    r.judge = await reviewApi("/api/review/judge",
      { company_id: c.id, finance_result: r.finance, tech_result: r.tech },    // 5.5:前兩支回應原封不動帶入
      MOCK.judge, 2000);
    phase.value = "done"; scrollCommittee();
  } catch (e) {
    err.value = e;        // 顯示 error.message + 重試按鈕(7.3)
    phase.value = "idle"; // phase 回到 idle(7.3)
    scrollCommittee();
  }
}

// ============================================================
// 瀑布圖:模板用的座標預計算(6.5:顏色由 type 決定,灰/綠/紅)
// ============================================================
function wfBars(items) {
  let cursor = 0;
  return items.map((it) => {
    const start = it.type === "base" ? 0 : cursor;
    const left = it.value >= 0 ? start : start + it.value;
    const width = Math.abs(it.value);
    cursor = start + it.value;
    return {
      ...it, left, width,
      bar: it.type === "base" ? "bg-slate-400" : it.type === "plus" ? "bg-emerald-600" : "bg-rose-600",
      tc: it.type === "base" ? "text-slate-600" : it.type === "plus" ? "text-emerald-700" : "text-rose-700",
      display: it.type === "base" ? String(it.value) : (it.value > 0 ? "+" : "") + it.value,
    };
  });
}

// ============================================================
// 頁籤 2:拜訪前情資(手刻 SVG 雷達圖,取代 recharts)
// ============================================================
const sel = ref("finance");
const selDim = computed(() => MOCK.radar.find((x) => x.key === sel.value));
const weakest = [...MOCK.radar].sort((a, b) => a.score - b.score)[0];

const R_CX = 160, R_CY = 140, R_R = 96;
function radarPt(i, val, r = R_R) {
  const a = (Math.PI * 2 * i) / MOCK.radar.length - Math.PI / 2;
  return [R_CX + Math.cos(a) * (val / 100) * r, R_CY + Math.sin(a) * (val / 100) * r];
}
function radarPoly(field) {
  return MOCK.radar.map((d, i) => radarPt(i, d[field]).join(",")).join(" ");
}
const radarGrid = [25, 50, 75, 100].map((lv) => MOCK.radar.map((_, i) => radarPt(i, lv).join(",")).join(" "));
const radarAxes = MOCK.radar.map((_, i) => radarPt(i, 100));
const radarLabels = MOCK.radar.map((d, i) => {
  const [x, y] = radarPt(i, 122);
  const a = (Math.PI * 2 * i) / MOCK.radar.length - Math.PI / 2;
  const cos = Math.cos(a);
  const anchor = Math.abs(cos) < 0.3 ? "middle" : cos > 0 ? "start" : "end";
  return { ...d, x, y: y + 4, anchor };
});

// ============================================================
// 頁籤 3:拜訪中提詞
// ※ /api/interview/assess 未列入規格書 v1.0;若要真串接需先提 v1.1 契約,
//   否則 Demo 期維持前端 Mock(下方 assess 函式)
// ============================================================
const qs = ref(MOCK.questions.map((q) => ({ ...q, status: q.id === 1 ? "active" : "pending" })));
const activeId = ref(1);
const answerInput = ref("");
const midBusy = ref(false);
const midRes = ref(null);
const rec = ref(false);
let recTimer = null;
const activeQ = computed(() => qs.value.find((q) => q.id === activeId.value));
const doneCount = computed(() => qs.value.filter((q) => q.status === "resolved").length);

function pickQ(id) { activeId.value = id; answerInput.value = ""; midRes.value = null; }

function assess(answer) {
  if (/(已簽|簽約|核貸|承諾函|保證)/.test(answer))
    return { verdict: "resolved", reason: "客戶提出具法律效力之資金承諾,量級相符,風險點視為化解。", follow: "建議索取文件副本附入審查報告。" };
  if (/(意向|洽談|規劃|預計|評估|募資|B輪|b輪)/.test(answer))
    return { verdict: "partial", reason: "提出資金方向但屬意向性質、未具約束力,時程未完全對上。", follow: "追問:意向書是否具法律約束力?交割時點?募資延遲的備援方案?" };
  return { verdict: "unresolved", reason: "回答未提出具體來源或時程,風險點未化解。", follow: "追問:請以數字說明缺口金額、資金來源、到位時間三項。" };
}

function toggleRec() {
  if (rec.value) { clearInterval(recTimer); rec.value = false; return; }
  const demo = "我們已取得兩家創投的B輪投資意向書,預計第四季完成募資,金額約八億。";
  let i = 0; answerInput.value = ""; rec.value = true;
  recTimer = setInterval(() => {
    i += 3; answerInput.value = demo.slice(0, i);
    if (i >= demo.length) { clearInterval(recTimer); rec.value = false; }
  }, 80);
}

async function submitAnswer() {
  if (!answerInput.value.trim() || midBusy.value) return;
  midBusy.value = true; midRes.value = null;
  await sleep(1400); // [API] /api/interview/assess ※未列入規格書 v1.0,需提 v1.1
  const res = assess(answerInput.value);
  midRes.value = res;
  qs.value = qs.value.map((q) => (q.id === activeId.value ? { ...q, status: res.verdict } : q));
  midBusy.value = false;
}

// ============================================================
// 頁籤 4:拜訪後評分
// ============================================================
const SAMPLE_NOTES = `7/16 下午拜訪,出席:財務長林OO、技術長張OO。
資金缺口:已取得兩家創投B輪意向書約8億,預計Q4交割,尚未簽署具約束力文件。
良率:試產線63%,損益兩平需75%,預計明年Q2達標,已與設備商簽改善合約。
客戶集中:承認最大客戶即專利主要引用方,合約2027到期,續約洽談中、第三家客戶送樣。
新資訊:廠房二期已動工,將再投入12億(原財報未揭露)。
承諾8/15前提供:意向書副本、良率改善合約。`;

const notes = ref(SAMPLE_NOTES);
const postStage = ref("idle");
const ext = ref(null);
const sc = ref(null);
const postBusy = computed(() => postStage.value === "extracting" || postStage.value === "scoring");

async function runPost() {
  ext.value = null; sc.value = null; postStage.value = "extracting";
  await sleep(1700); ext.value = MOCK.postExtract; postStage.value = "extracted"; // [API] /api/postvisit/extract ※未列入規格書 v1.0,需提 v1.1
  await sleep(1100); postStage.value = "scoring";
  await sleep(1500); sc.value = MOCK.postScore; postStage.value = "done";         // [API] /api/postvisit/score   ※未列入規格書 v1.0,需提 v1.1
}

// 5.6:此 API 允許最後實作,先以按鈕+提示佔位;整合時改為
// callApi("/api/report", { company_id, judge_result }) → window.open(res.report_url, "_blank")
function makeReport() { alert("Demo:呼叫 POST /api/report 產出 PDF"); }
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-800 flex flex-col"
    :style="{ fontFamily: `'Noto Sans TC','PingFang TC','Microsoft JhengHei',sans-serif`, fontSize, colorScheme: 'light' }">

    <a href="#main" class="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:top-2 focus:left-2 focus:px-3 focus:py-2 focus:bg-sky-900 focus:text-white focus:rounded-sm">
      跳至主要內容
    </a>

    <!-- 上方工具列(深色細帶):政府網站標配 -->
    <div class="bg-sky-950 text-sky-100 text-xs">
      <div class="max-w-5xl mx-auto px-4 h-8 flex items-center justify-between">
        <span>精誠 SEI 競賽展示系統 · 非正式金融服務</span>
        <div class="flex items-center gap-3">
          <a href="#" @click.prevent :class="`hover:underline underline-offset-2 rounded-sm px-0.5 ${focusRing}`">網站導覽</a>
          <span aria-hidden="true" class="text-sky-800">|</span>
          <span class="flex items-center gap-1" role="group" aria-label="字級調整">
            字級
            <button v-for="s in fontSizes" :key="s.k" @click="fontScale = s.k" :aria-pressed="fontScale === s.k"
              :class="[`w-6 h-6 rounded-sm ${focusRing}`, fontScale === s.k ? 'bg-sky-100 text-sky-950 font-bold' : 'hover:bg-sky-800']">
              {{ s.label }}
            </button>
          </span>
        </div>
      </div>
    </div>

    <!-- Header -->
    <header class="bg-white border-b-4 border-sky-900">
      <div class="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between gap-6 flex-wrap">
        <button @click="onNav('案件總覽')" :class="`flex items-center gap-3 rounded-sm ${focusRing}`">
          <span aria-hidden="true" class="grid place-items-center w-11 h-11 rounded-sm bg-sky-900 text-white">
            <svg viewBox="0 0 24 24" class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /><path d="M8 11h6M11 8v6" />
            </svg>
          </span>
          <span class="text-left">
            <span class="block text-xl font-bold text-sky-950 leading-tight">智貸先鋒 企業授信情資服務網</span>
            <span class="block text-xs text-slate-500 leading-tight tracking-wide">Credit-Lens Corporate Credit Intelligence</span>
          </span>
        </button>
        <nav aria-label="主選單">
          <ul class="flex items-center gap-1">
            <li v-for="t in navItems" :key="t">
              <button @click="onNav(t)" :aria-current="nav === t ? 'page' : undefined"
                :class="[`px-3 py-2 text-sm font-medium border-b-2 motion-safe:transition-colors ${focusRing}`,
                  nav === t ? 'border-sky-800 text-sky-900 font-bold' : 'border-transparent text-slate-600 hover:text-sky-900 hover:border-sky-300']">
                {{ t }}
              </button>
            </li>
          </ul>
        </nav>
      </div>
    </header>

    <!-- Hero 色帶:標語 + 大搜尋框 + 統計數字(data.taipei 式) -->
    <div v-if="page === 'dashboard'" class="bg-sky-900 text-white">
      <div class="max-w-5xl mx-auto px-4 py-8">
        <h1 class="text-2xl font-bold mb-1">多源情資交叉驗證,開啟新興產業授信新視野</h1>
        <p class="text-sky-200 text-sm mb-5">整合財報、專利、裁判書、裁罰紀錄等 7 項公開資料源,由 AI 審查委員會為每一件授信案把關。</p>
        <form role="search" @submit.prevent class="flex max-w-2xl">
          <label for="case-search" class="sr-only">搜尋案件</label>
          <input id="case-search" type="search" v-model="query"
            placeholder="請輸入公司名稱或統一編號…" autocomplete="off" spellcheck="false"
            :class="`flex-1 h-12 px-4 text-slate-900 bg-white rounded-l-sm placeholder-slate-400 ${focusRing}`" />
          <button type="submit" :class="`h-12 px-6 bg-amber-500 hover:bg-amber-400 text-sky-950 font-bold rounded-r-sm motion-safe:transition-colors ${focusRing}`">
            搜尋
          </button>
        </form>
        <dl class="flex gap-8 mt-6 text-sm flex-wrap">
          <div v-for="[k, v] in [['介接資料源', '7 項'], ['進行中案件', '3 件'], ['本月 AI 分析', '128 次']]" :key="k" class="flex items-baseline gap-2">
            <dt class="text-sky-300">{{ k }}</dt>
            <dd :class="`${num} text-xl font-bold`">{{ v }}</dd>
          </div>
        </dl>
      </div>
    </div>

    <div class="flex-1">
      <!-- ================= 頁面 1:案件總覽 ================= -->
      <main v-if="page === 'dashboard'" id="main" class="max-w-5xl mx-auto px-4 py-6 w-full">
        <nav aria-label="麵包屑" class="text-sm text-slate-500">
          <ol class="flex items-center gap-1 flex-wrap">
            <li>首頁</li>
            <li class="flex items-center gap-1"><span aria-hidden="true" class="text-slate-400 px-0.5">/</span><span aria-current="page" class="text-slate-700">案件總覽</span></li>
          </ol>
        </nav>

        <div class="mt-4">
          <div class="flex items-center justify-between gap-4 mb-3">
            <h2 class="border-l-4 border-sky-800 pl-3 text-lg font-bold text-slate-900">
              進行中案件<span v-if="query.trim()" class="text-sm font-normal text-slate-500">(搜尋:「{{ query.trim() }}」,共 {{ caseList.length }} 件)</span>
            </h2>
            <button :class="`px-4 py-2 text-sm font-bold text-white bg-sky-900 hover:bg-sky-800 rounded-sm motion-safe:transition-colors ${focusRing}`">
              + 新增授信案件
            </button>
          </div>

          <div v-if="caseList.length === 0" class="border border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
            查無符合的案件,請調整搜尋條件。
          </div>
          <ul v-else class="border-t-2 border-sky-900">
            <li v-for="c in caseList" :key="c.id" class="border-b border-slate-300">
              <button @click="openCase(c)"
                :class="`w-full text-left bg-white hover:bg-sky-50 px-4 py-3.5 flex items-center gap-4 flex-wrap motion-safe:transition-colors group ${focusRing}`">
                <span :class="`${num} text-xs text-slate-500 w-24 shrink-0`">{{ c.updated }}</span>
                <span class="text-xs px-1.5 py-0.5 border border-sky-300 bg-sky-50 text-sky-900 rounded-sm shrink-0">{{ c.industry }}</span>
                <span class="flex-1 min-w-48">
                  <span class="text-slate-900 font-medium group-hover:text-sky-900 group-hover:underline underline-offset-2">{{ c.name }}</span>
                  <span :class="`block text-xs text-slate-500 mt-0.5 ${num}`">統一編號 {{ c.id }}</span>
                </span>
                <span class="text-xs text-slate-600 w-24">目前階段:<span class="font-medium text-slate-800">{{ STAGE_LABEL[c.stage] }}</span></span>
                <span class="w-16 text-right">
                  <span v-if="c.score !== null" :class="`${num} font-bold text-lg text-sky-900`">{{ c.score }}<span class="text-xs text-slate-500 font-normal"> 分</span></span>
                  <span v-else class="text-xs text-slate-400">評分中</span>
                </span>
              </button>
            </li>
          </ul>
        </div>

        <div class="mt-8">
          <div class="flex items-center justify-between gap-4 mb-3">
            <h2 class="border-l-4 border-sky-800 pl-3 text-lg font-bold text-slate-900">最新公告</h2>
          </div>
          <ul class="border-t-2 border-sky-900">
            <li v-for="([d, tg, t], i) in announcements" :key="i" class="border-b border-slate-300 bg-white px-4 py-3 flex items-center gap-3 text-sm flex-wrap">
              <span :class="`${num} text-xs text-slate-500 w-24 shrink-0`">{{ d }}</span>
              <span class="text-xs px-1.5 py-0.5 border border-amber-400 bg-amber-50 text-amber-800 rounded-sm shrink-0">{{ tg }}</span>
              <a href="#" @click.prevent :class="`text-slate-800 hover:text-sky-900 hover:underline underline-offset-2 rounded-sm ${focusRing}`">{{ t }}</a>
            </li>
          </ul>
        </div>
      </main>

      <!-- ================= 頁面 2:案件詳情 ================= -->
      <main v-else id="main" class="max-w-5xl mx-auto px-4 py-5 w-full">
        <nav aria-label="麵包屑" class="text-sm text-slate-500">
          <ol class="flex items-center gap-1 flex-wrap">
            <li><button @click="goHome" :class="`text-sky-800 hover:underline underline-offset-2 rounded-sm px-0.5 ${focusRing}`">首頁</button></li>
            <li class="flex items-center gap-1"><span aria-hidden="true" class="text-slate-400 px-0.5">/</span>
              <button @click="goHome" :class="`text-sky-800 hover:underline underline-offset-2 rounded-sm px-0.5 ${focusRing}`">案件總覽</button></li>
            <li class="flex items-center gap-1"><span aria-hidden="true" class="text-slate-400 px-0.5">/</span><span aria-current="page" class="text-slate-700">{{ current.name }}</span></li>
          </ol>
        </nav>

        <div class="mt-4 mb-4 pb-3 border-b border-slate-300 flex items-end justify-between gap-4 flex-wrap">
          <div>
            <h1 class="text-2xl font-bold text-slate-900">{{ current.name }}</h1>
            <p :class="`text-sm text-slate-500 mt-1 ${num}`">統一編號 {{ current.id }} · {{ current.industry }} · 最近更新 {{ current.updated }}</p>
          </div>
          <div v-if="current.score !== null" class="text-right">
            <div class="text-xs text-slate-500">目前綜合評分</div>
            <span :class="`${num} font-bold text-3xl text-sky-900`">{{ current.score }}<span class="text-xs text-slate-500 font-normal"> 分</span></span>
          </div>
        </div>

        <!-- 頁籤:政府網站常見的方塊型頁籤(作用中=深藍底白字) -->
        <div role="tablist" aria-label="工作流階段" class="flex flex-wrap gap-1 border-b-2 border-sky-900">
          <button v-for="(t, i) in TABS" :key="t.key" role="tab" :aria-selected="tab === t.key" :id="`tab-${t.key}`" :aria-controls="`panel-${t.key}`"
            @click="tab = t.key"
            :class="[`px-4 py-2.5 text-sm rounded-t-sm border border-b-0 motion-safe:transition-colors ${focusRing}`,
              tab === t.key ? 'bg-sky-900 border-sky-900 text-white font-bold' : 'bg-slate-100 border-slate-300 text-slate-700 hover:bg-sky-50 hover:text-sky-900']">
            <span :class="[`${num} mr-1.5`, tab === t.key ? 'text-sky-300' : 'text-slate-400']">{{ i + 1 }}.</span>
            {{ t.label }}
          </button>
        </div>

        <div class="pt-4 pb-2" role="tabpanel" :id="`panel-${tab}`" :aria-labelledby="`tab-${tab}`">

          <!-- ========== 頁籤 1:AI 審查會議 ========== -->
          <div v-if="tab === 'committee'" class="space-y-3">
            <div class="bg-sky-50 border border-sky-200 px-4 py-3 flex items-center justify-between gap-4 flex-wrap">
              <p class="text-sm text-slate-700">由財務、技術兩位分析 Agent 發言,風險審查官交叉質詢後裁決基準分。</p>
              <button @click="runCommittee(false)" :disabled="busy"
                :class="`px-4 py-2 text-sm font-bold text-white bg-sky-900 hover:bg-sky-800 disabled:bg-slate-300 disabled:text-slate-500 rounded-sm motion-safe:transition-colors ${focusRing}`">
                {{ busy ? "審查進行中…" : phase === "done" ? "重新召開會議" : "召開審查會議" }}
              </button>
            </div>

            <div v-if="phase === 'idle' && !r.finance && !err" class="bg-white border border-dashed border-slate-400 py-12 text-center text-sm text-slate-500">
              尚未召開審查會議。
            </div>

            <div v-if="err" role="alert" class="border border-rose-300 border-l-4 border-l-rose-600 bg-rose-50 p-4 flex items-center justify-between gap-4 flex-wrap">
              <div>
                <div class="font-bold text-rose-800 text-sm mb-0.5">審查中斷({{ err.code }})</div>
                <p class="text-sm text-slate-800 leading-relaxed">{{ err.message }}</p>
              </div>
              <button @click="runCommittee(true)"
                :class="`px-5 h-10 text-sm font-bold text-white bg-rose-700 hover:bg-rose-600 rounded-sm motion-safe:transition-colors ${focusRing}`">
                重試
              </button>
            </div>

            <!-- 財務分析 Agent -->
            <div v-if="phase === 'finance' || r.finance"
              :class="`bg-white border border-slate-300 border-l-4 ${AGENT.finance.edge} p-4 motion-safe:animate-[fadeUp_.4s_ease-out]`">
              <div :class="`font-bold text-sm mb-2.5 ${AGENT.finance.text}`">{{ AGENT.finance.name }} Agent</div>
              <div v-if="!r.finance" class="text-sm text-slate-500">分析中<span class="animate-pulse" aria-hidden="true"> …</span></div>
              <template v-else>
                <div class="text-right -mt-7 mb-1">
                  <span :class="`${num} font-bold text-xl text-amber-800`">{{ r.finance.score }}<span class="text-xs text-slate-500 font-normal"> 分</span></span>
                </div>
                <div v-for="(f, i) in r.finance.findings" :key="i" class="mb-2 text-sm leading-relaxed text-slate-800">
                  {{ f.text }}<br />
                  <span class="inline-block mt-1 mr-1 px-1.5 py-0.5 rounded-sm text-xs bg-slate-100 text-slate-600 border border-slate-300">資料來源:{{ f.cite }}</span>
                  <span v-if="f.confidence != null" :class="`inline-block mt-1 mr-1 px-1.5 py-0.5 rounded-sm text-xs bg-white text-slate-500 border border-slate-300 ${num}`">信心 {{ Math.round(f.confidence * 100) }}%</span>
                </div>
              </template>
            </div>

            <!-- 技術情報 Agent -->
            <div v-if="phase === 'tech' || r.tech"
              :class="`bg-white border border-slate-300 border-l-4 ${AGENT.tech.edge} p-4 motion-safe:animate-[fadeUp_.4s_ease-out]`">
              <div :class="`font-bold text-sm mb-2.5 ${AGENT.tech.text}`">{{ AGENT.tech.name }} Agent</div>
              <div v-if="!r.tech" class="text-sm text-slate-500">分析中<span class="animate-pulse" aria-hidden="true"> …</span></div>
              <template v-else>
                <div class="text-right -mt-7 mb-1">
                  <span :class="`${num} font-bold text-xl text-cyan-800`">{{ r.tech.score }}<span class="text-xs text-slate-500 font-normal"> 分</span></span>
                </div>
                <div v-for="(f, i) in r.tech.findings" :key="i" class="mb-2 text-sm leading-relaxed text-slate-800">
                  {{ f.text }}<br />
                  <span class="inline-block mt-1 mr-1 px-1.5 py-0.5 rounded-sm text-xs bg-slate-100 text-slate-600 border border-slate-300">資料來源:{{ f.cite }}</span>
                  <span v-if="f.confidence != null" :class="`inline-block mt-1 mr-1 px-1.5 py-0.5 rounded-sm text-xs bg-white text-slate-500 border border-slate-300 ${num}`">信心 {{ Math.round(f.confidence * 100) }}%</span>
                </div>
              </template>
            </div>

            <!-- 風險審查官 Agent -->
            <div v-if="phase === 'judge' || r.judge"
              :class="`bg-white border border-slate-300 border-l-4 ${AGENT.judge.edge} p-4 motion-safe:animate-[fadeUp_.4s_ease-out]`">
              <div :class="`font-bold text-sm mb-2.5 ${AGENT.judge.text}`">{{ AGENT.judge.name }} Agent</div>
              <div v-if="!r.judge" class="text-sm text-slate-500">分析中<span class="animate-pulse" aria-hidden="true"> …</span></div>
              <template v-else>
                <!-- 6.3:contradictions 可為空陣列,顯示「無重大矛盾」 -->
                <div v-if="r.judge.contradictions.length === 0" class="text-sm text-slate-700 mb-2.5 border border-emerald-300 bg-emerald-50 p-3">
                  交叉質詢完成,無重大矛盾。
                </div>
                <div v-else class="text-sm text-slate-600 mb-2.5">交叉質詢完成,發現 {{ r.judge.contradictions.length }} 項矛盾:</div>
                <div v-for="(x, i) in r.judge.contradictions" :key="i"
                  :class="['mb-2 border p-3', (SEVERITY[x.severity] || SEVERITY.medium).box]">
                  <div class="text-rose-800 font-bold text-sm mb-1 flex items-center gap-2">
                    <span>【矛盾 {{ i + 1 }}】{{ x.title }}</span>
                    <span :class="['text-xs font-normal px-1.5 py-0.5 border rounded-sm', (SEVERITY[x.severity] || SEVERITY.medium).chip]">
                      嚴重度:{{ (SEVERITY[x.severity] || SEVERITY.medium).label }}
                    </span>
                  </div>
                  <div class="text-sm text-slate-800 leading-relaxed">{{ x.detail }}</div>
                </div>
                <div class="mt-3 text-sm leading-relaxed text-slate-900 bg-slate-50 border border-slate-200 p-3">
                  <span class="font-bold text-rose-800">裁決:</span>{{ r.judge.verdict }}
                </div>
              </template>
            </div>

            <!-- 拜訪前基準評分(瀑布圖) -->
            <div v-if="phase === 'done' && r.judge" class="bg-white border border-slate-300 border-t-4 border-t-sky-900 p-4 motion-safe:animate-[fadeUp_.4s_ease-out]">
              <h3 class="font-bold text-slate-900 mb-3">拜訪前基準評分</h3>
              <div class="space-y-1.5">
                <div v-for="(it, i) in wfBars(r.judge.waterfall)" :key="i" class="flex items-center gap-3 text-sm">
                  <div class="w-28 text-slate-700 text-right shrink-0 text-xs">{{ it.label }}</div>
                  <div class="flex-1 h-4 bg-slate-100 border border-slate-200 relative overflow-hidden">
                    <div :class="`absolute h-full ${it.bar} motion-safe:transition-[left,width] motion-safe:duration-700`"
                      :style="{ left: `${it.left}%`, width: `${it.width}%` }" />
                  </div>
                  <div :class="`w-10 ${num} text-sm text-right ${it.tc}`">{{ it.display }}</div>
                </div>
                <div class="flex items-center justify-between pt-2 mt-1 border-t-2 border-slate-300">
                  <span class="text-sm font-bold text-slate-900">綜合評分</span>
                  <span :class="`${num} font-bold text-2xl text-sky-900`">{{ r.judge.final_score }}<span class="text-xs text-slate-500 font-normal"> 分</span></span>
                </div>
              </div>
            </div>
            <div ref="committeeEnd" />
          </div>

          <!-- ========== 頁籤 2:拜訪前情資 ========== -->
          <div v-else-if="tab === 'pre'" class="space-y-5">
            <div class="grid lg:grid-cols-2 gap-4">
              <div class="bg-white border border-slate-300 p-3">
                <h3 class="text-sm font-bold text-slate-900 border-l-4 border-sky-800 pl-2 mb-1">護城河雷達圖</h3>
                <!-- 手刻 SVG 雷達圖(取代 recharts;點選維度名稱可切換) -->
                <svg viewBox="0 0 320 290" class="w-full" style="max-height: 290px" role="img" aria-label="六維護城河雷達圖">
                  <polygon v-for="(pts, i) in radarGrid" :key="'g' + i" :points="pts" fill="none" stroke="#cbd5e1" stroke-width="1" />
                  <line v-for="([ax, ay], i) in radarAxes" :key="'a' + i" :x1="R_CX" :y1="R_CY" :x2="ax" :y2="ay" stroke="#cbd5e1" stroke-width="1" />
                  <polygon :points="radarPoly('benchmark')" fill="#94a3b8" fill-opacity="0.12" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4 4" />
                  <polygon :points="radarPoly('score')" fill="#0369a1" fill-opacity="0.22" stroke="#0c4a6e" stroke-width="2" />
                  <text v-for="lb in radarLabels" :key="lb.key" :x="lb.x" :y="lb.y" :text-anchor="lb.anchor"
                    :fill="lb.key === sel ? '#0c4a6e' : '#475569'" :font-size="12" :font-weight="lb.key === sel ? 700 : 400"
                    style="cursor: pointer" @click="sel = lb.key">
                    {{ lb.label }} {{ lb.score }}
                  </text>
                </svg>
                <div class="flex justify-center gap-5 text-xs text-slate-600 mt-1">
                  <span class="flex items-center gap-1.5"><span class="inline-block w-4 h-0.5 bg-sky-900" />該企業</span>
                  <span class="flex items-center gap-1.5"><span class="inline-block w-4 border-t-2 border-dashed border-slate-400" />產業基準</span>
                </div>
                <p class="text-xs text-slate-500 text-center mt-1">點選維度名稱可查看評分理由與資料來源</p>
              </div>

              <div class="space-y-3">
                <div class="bg-white border border-slate-300 border-t-4 border-t-sky-900 p-4">
                  <div class="flex items-baseline justify-between mb-1.5 gap-2">
                    <h3 class="font-bold text-slate-900">{{ selDim.label }}</h3>
                    <span :class="`${num} font-bold text-xl text-sky-900`">{{ selDim.score }}<span class="text-xs text-slate-500 font-normal"> 分</span></span>
                  </div>
                  <div class="flex items-center gap-2 text-xs mb-2.5 flex-wrap">
                    <span :class="['px-1.5 py-0.5 border rounded-sm', AGENT[selDim.agent].chip]">評分:{{ AGENT[selDim.agent].name }} Agent</span>
                    <span :class="`text-slate-500 ${num}`">產業基準 {{ selDim.benchmark }} 分({{ selDim.score >= selDim.benchmark ? "高於" : "低於" }}基準 {{ Math.abs(selDim.score - selDim.benchmark) }} 分)</span>
                  </div>
                  <p class="text-sm leading-relaxed text-slate-800 mb-1.5">{{ selDim.reason }}</p>
                  <span v-for="(ct, i) in selDim.cites" :key="i" class="inline-block mt-1 mr-1 px-1.5 py-0.5 rounded-sm text-xs bg-slate-100 text-slate-600 border border-slate-300">資料來源:{{ ct }}</span>
                </div>
                <div class="bg-amber-50 border border-amber-300 border-l-4 border-l-amber-500 p-4 text-sm leading-relaxed">
                  <div class="font-bold text-amber-900 mb-1">本次拜訪建議聚焦</div>
                  <p class="text-slate-800">
                    最弱維度為「{{ weakest.label }}」({{ weakest.score }} 分,低於產業基準 {{ weakest.benchmark - weakest.score }} 分),
                    下方防禦提問單已優先針對此維度生成追問。
                  </p>
                </div>
              </div>
            </div>

            <div>
              <div class="flex items-center justify-between gap-4 mb-3">
                <h2 class="border-l-4 border-sky-800 pl-3 text-lg font-bold text-slate-900">護城河防禦提問單</h2>
              </div>
              <ol class="border-t-2 border-sky-900">
                <li v-for="q in MOCK.questions" :key="q.id" class="bg-white border-b border-slate-300 px-4 py-3 hover:bg-sky-50 motion-safe:transition-colors">
                  <div class="flex gap-3">
                    <span :class="`${num} text-sky-900 font-bold text-sm shrink-0 w-8`">Q{{ q.id }}.</span>
                    <div class="min-w-0">
                      <p class="text-sm text-slate-900 font-medium leading-relaxed">{{ q.q }}</p>
                      <p class="text-xs text-slate-500 mt-1 leading-relaxed">
                        <span class="px-1 py-0.5 bg-slate-100 border border-slate-300 rounded-sm mr-1">AI 出題依據</span>
                        {{ q.why }}
                      </p>
                    </div>
                  </div>
                </li>
              </ol>
            </div>
          </div>

          <!-- ========== 頁籤 3:拜訪中提詞 ========== -->
          <div v-else-if="tab === 'mid'" class="grid lg:grid-cols-5 gap-4">
            <!-- 左:風險點清單(政府列表風) -->
            <div class="lg:col-span-2">
              <h3 class="text-sm font-bold text-slate-900 border-l-4 border-sky-800 pl-2 mb-2">
                風險點清單(已化解 <span :class="num">{{ doneCount }}/{{ qs.length }}</span>)
              </h3>
              <ul class="border-t-2 border-sky-900">
                <li v-for="q in qs" :key="q.id" class="border-b border-slate-300">
                  <button @click="pickQ(q.id)" :aria-current="q.id === activeId ? 'true' : undefined"
                    :class="[`w-full text-left px-3 py-2.5 text-sm flex items-center gap-2 motion-safe:transition-colors ${focusRing}`,
                      q.id === activeId ? 'bg-sky-900 text-white' : 'bg-white hover:bg-sky-50 text-slate-800']">
                    <span :class="`${num} font-bold shrink-0`">Q{{ q.id }}</span>
                    <span class="flex-1 min-w-0 truncate">{{ q.dim }}</span>
                    <span v-if="VERDICT[q.status]"
                      :class="['text-xs px-1.5 py-0.5 border rounded-sm shrink-0', q.id === activeId ? 'bg-white' : '', VERDICT[q.status].cls]">
                      {{ VERDICT[q.status].label }}
                    </span>
                    <span v-else :class="['text-xs shrink-0', q.id === activeId ? 'text-sky-200' : 'text-slate-400']">
                      {{ q.id === activeId ? "進行中" : "待提問" }}
                    </span>
                  </button>
                </li>
              </ul>
              <p class="text-xs text-slate-500 mt-2 leading-relaxed">
                行動版介面同步提供;面談時輸入客戶回答,AI 即時判定風險是否化解。
              </p>
            </div>

            <!-- 右:提問與判定 -->
            <div class="lg:col-span-3 space-y-3">
              <div class="bg-white border border-slate-300 border-l-4 border-l-sky-600 p-4">
                <div :class="`text-xs text-sky-900 font-bold mb-1 ${num}`">問題 {{ activeQ.id }}/{{ qs.length }} · {{ activeQ.dim }}</div>
                <p class="text-sm text-slate-900 leading-relaxed font-medium">{{ activeQ.q }}</p>
                <p class="mt-1.5 text-xs text-slate-500 leading-relaxed">AI 出題依據:{{ activeQ.why }}</p>
              </div>

              <div class="bg-white border border-slate-300 p-4">
                <div class="text-xs text-slate-600 mb-1.5 flex items-center justify-between">
                  <label for="ans" class="font-bold">客戶回答(輸入或口述)</label>
                  <span v-if="rec" class="text-rose-700 motion-safe:animate-pulse">● 語音轉文字中…</span>
                </div>
                <textarea id="ans" v-model="answerInput" rows="3"
                  placeholder="請輸入客戶的回答,或按「語音輸入」口述…" spellcheck="false"
                  :class="`w-full border border-slate-300 p-2.5 text-sm text-slate-800 resize-none placeholder-slate-400 rounded-sm focus:border-sky-700 ${focusRing}`" />
                <div class="flex gap-2 mt-2">
                  <button @click="toggleRec"
                    :class="[`px-4 h-10 text-sm font-bold rounded-sm border motion-safe:transition-colors ${focusRing}`,
                      rec ? 'bg-rose-700 border-rose-700 text-white' : 'bg-white border-slate-400 text-slate-700 hover:bg-slate-100']">
                    {{ rec ? "停止" : "語音輸入" }}
                  </button>
                  <button @click="submitAnswer" :disabled="midBusy || !answerInput.trim()"
                    :class="`flex-1 h-10 text-sm font-bold text-white bg-sky-900 hover:bg-sky-800 disabled:bg-slate-300 disabled:text-slate-500 rounded-sm motion-safe:transition-colors ${focusRing}`">
                    {{ midBusy ? "AI 判定中…" : "送出判定" }}
                  </button>
                </div>
              </div>

              <div v-if="midBusy" class="bg-white border border-slate-300 p-3.5 text-sm text-slate-500" aria-live="polite">
                風險審查官比對回答與風險點中<span class="animate-pulse" aria-hidden="true"> …</span>
              </div>
              <div v-if="midRes" aria-live="polite"
                :class="['border border-l-4 p-4 motion-safe:animate-[fadeUp_.35s_ease-out]', VERDICT[midRes.verdict].cls,
                  midRes.verdict === 'resolved' ? 'border-l-emerald-600' : midRes.verdict === 'partial' ? 'border-l-amber-500' : 'border-l-rose-600']">
                <div class="font-bold text-sm mb-1.5">判定結果:{{ VERDICT[midRes.verdict].label }}</div>
                <p class="text-sm text-slate-800 leading-relaxed mb-2">{{ midRes.reason }}</p>
                <div class="bg-white border border-slate-300 p-2.5 text-sm leading-relaxed">
                  <span class="font-bold text-sky-900">建議追問:</span>
                  <span class="text-slate-800"> {{ midRes.follow }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- ========== 頁籤 4:拜訪後評分 ========== -->
          <div v-else-if="tab === 'post'" class="space-y-4">
            <div class="bg-white border border-slate-300 p-4">
              <label for="notes" class="block text-sm font-bold text-slate-900 mb-2">
                會議紀錄<span class="ml-2 text-xs font-normal text-slate-500">貼上自由格式紀錄,AI 自動結構化萃取</span>
              </label>
              <textarea id="notes" v-model="notes" rows="7" spellcheck="false"
                :class="`w-full border border-slate-300 p-3 text-sm leading-relaxed text-slate-800 resize-none rounded-sm bg-slate-50 focus:bg-white focus:border-sky-700 ${focusRing}`" />
              <button @click="runPost" :disabled="postBusy || !notes.trim()"
                :class="`mt-2.5 px-6 h-10 text-sm font-bold text-white bg-sky-900 hover:bg-sky-800 disabled:bg-slate-300 disabled:text-slate-500 rounded-sm motion-safe:transition-colors ${focusRing}`">
                {{ postBusy ? "分析中…" : "開始分析" }}
              </button>
            </div>

            <div v-if="postStage === 'extracting'" class="bg-white border border-slate-300 p-4 text-sm text-slate-500" aria-live="polite">
              結構化萃取中:承諾事項/風險回應/新發現風險<span class="animate-pulse" aria-hidden="true"> …</span>
            </div>

            <div v-if="ext" class="bg-white border border-slate-300 border-t-4 border-t-sky-900 p-4 space-y-4 motion-safe:animate-[fadeUp_.4s_ease-out]">
              <h3 class="font-bold text-slate-900">結構化萃取結果</h3>

              <div>
                <div class="text-xs font-bold text-slate-700 mb-1.5">一、承諾事項({{ ext.commitments.length }} 項,自動列入追蹤)</div>
                <table class="w-full text-sm border-collapse">
                  <thead>
                    <tr class="bg-slate-100 text-slate-700 text-xs">
                      <th scope="col" class="border border-slate-300 px-2 py-1.5 text-left font-bold">承諾內容</th>
                      <th scope="col" class="border border-slate-300 px-2 py-1.5 text-left font-bold w-28">承諾人</th>
                      <th scope="col" class="border border-slate-300 px-2 py-1.5 text-left font-bold w-28">期限</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(cm, i) in ext.commitments" :key="i" class="hover:bg-sky-50">
                      <td class="border border-slate-300 px-2 py-1.5 text-slate-800">{{ cm.item }}</td>
                      <td class="border border-slate-300 px-2 py-1.5 text-slate-600">{{ cm.owner }}</td>
                      <td :class="`border border-slate-300 px-2 py-1.5 text-amber-800 ${num}`">{{ cm.due }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div>
                <div class="text-xs font-bold text-slate-700 mb-1.5">二、風險點回應(對應防禦提問單)</div>
                <div v-for="(rp, i) in ext.responses" :key="i"
                  class="border border-slate-300 border-t-0 first:border-t px-3 py-2 flex items-center gap-3 flex-wrap hover:bg-sky-50">
                  <span class="text-sm text-slate-900 font-medium w-44 shrink-0">{{ rp.risk }}</span>
                  <span class="text-xs text-slate-600 flex-1 min-w-40">{{ rp.summary }}</span>
                  <span :class="['text-xs px-1.5 py-0.5 border rounded-sm shrink-0', VERDICT[rp.verdict].cls]">{{ VERDICT[rp.verdict].label }}</span>
                </div>
              </div>

              <div v-if="ext.newRisks.length > 0">
                <div class="text-xs font-bold text-rose-800 mb-1.5">三、面談中新發現的風險</div>
                <div v-for="(n, i) in ext.newRisks" :key="i"
                  class="border border-rose-300 border-l-4 border-l-rose-600 bg-rose-50 p-3 text-sm text-slate-800 leading-relaxed">{{ n.text }}</div>
              </div>
            </div>

            <div v-if="postStage === 'scoring'" class="bg-white border border-slate-300 p-4 text-sm text-slate-500" aria-live="polite">
              比對拜訪前基準,計算增減項<span class="animate-pulse" aria-hidden="true"> …</span>
            </div>

            <div v-if="sc" class="bg-white border border-slate-300 border-t-4 border-t-emerald-600 p-4 motion-safe:animate-[fadeUp_.4s_ease-out]">
              <h3 class="font-bold text-slate-900 mb-3">評分瀑布 — 每一分的來源</h3>
              <div class="space-y-1.5">
                <div v-for="(it, i) in wfBars(sc.waterfall)" :key="i" class="flex items-center gap-3 text-sm">
                  <div class="w-28 text-slate-700 text-right shrink-0 text-xs">{{ it.label }}</div>
                  <div class="flex-1 h-4 bg-slate-100 border border-slate-200 relative overflow-hidden">
                    <div :class="`absolute h-full ${it.bar} motion-safe:transition-[left,width] motion-safe:duration-700`"
                      :style="{ left: `${it.left}%`, width: `${it.width}%` }" />
                  </div>
                  <div :class="`w-10 ${num} text-sm text-right ${it.tc}`">{{ it.display }}</div>
                </div>
                <div class="flex items-center justify-between pt-2 mt-1 border-t-2 border-slate-300">
                  <span class="text-sm font-bold text-slate-900">綜合評分</span>
                  <span :class="`${num} font-bold text-2xl text-sky-900`">{{ sc.final }}<span class="text-xs text-slate-500 font-normal"> 分</span></span>
                </div>
              </div>
              <div class="mt-4 bg-slate-50 border border-slate-300 p-3 text-sm leading-relaxed">
                <span class="font-bold text-sky-900">審查官建議:</span>
                <span class="text-slate-800"> {{ sc.rec }}</span>
              </div>
              <button @click="makeReport"
                :class="`mt-3 px-6 h-11 text-sm font-bold text-white bg-emerald-700 hover:bg-emerald-600 rounded-sm motion-safe:transition-colors ${focusRing}`">
                產出授信審查報告(PDF)
              </button>
            </div>
          </div>

        </div>
      </main>
    </div>

    <!-- Footer -->
    <footer class="bg-slate-800 text-slate-300 mt-12">
      <div class="max-w-5xl mx-auto px-4 py-8 grid gap-6 sm:grid-cols-3 text-sm">
        <div>
          <div class="text-white font-bold mb-2">智貸先鋒 企業授信情資服務網</div>
          <p class="text-xs leading-relaxed text-slate-400">
            主辦單位:精誠 SEI 競賽第 X 組<br />
            技術架構:Multi-Agent · GraphRAG · LLM-as-a-Judge<br />
            本站為競賽展示系統,所有企業資料皆為模擬情境。
          </p>
        </div>
        <div>
          <div class="text-white font-bold mb-2">介接資料來源</div>
          <ul class="text-xs space-y-1 text-slate-400">
            <li v-for="t in ['TWSE 公開資訊觀測站', '經濟部商工登記(data.gov.tw)', '司法院裁判書開放 API', '環境部裁罰紀錄/勞動部違規名單']" :key="t">
              <a href="#" @click.prevent :class="`hover:text-white hover:underline underline-offset-2 rounded-sm ${focusRing}`">{{ t }}</a>
            </li>
          </ul>
        </div>
        <div>
          <div class="text-white font-bold mb-2">網站資訊</div>
          <ul class="text-xs space-y-1 text-slate-400">
            <li v-for="t in ['隱私權及資訊安全政策', '政府資料開放授權條款', '網站導覽']" :key="t">
              <a href="#" @click.prevent :class="`hover:text-white hover:underline underline-offset-2 rounded-sm ${focusRing}`">{{ t }}</a>
            </li>
          </ul>
          <span class="inline-block mt-3 px-2 py-1 border border-slate-500 rounded-sm text-xs text-slate-300">
            通過 AA 無障礙規範(示意)
          </span>
        </div>
      </div>
      <div class="border-t border-slate-700">
        <div class="max-w-5xl mx-auto px-4 py-3 text-xs text-slate-500 flex justify-between flex-wrap gap-2">
          <span>建議使用 Chrome、Edge、Firefox、Safari 瀏覽器</span>
          <span>© 2026 Credit-Lens Team. All Rights Reserved.</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style>
@keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
button { touch-action: manipulation; }
</style>
