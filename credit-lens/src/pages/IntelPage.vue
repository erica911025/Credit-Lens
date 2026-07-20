<script setup>
// 頁面 3:情資查詢(不綁案件的多源原始情資查詢台)
// 定位:案件詳情頁是「AI 分析後的結論」,本頁展示「原始情資本身」,
//      並以企業關係圖譜(GraphRAG)推理隱藏風險。
import { ref, computed } from "vue";
import { focusRing, num } from "../constants.js";
import { INTEL, CASES } from "../mock.js";

const emit = defineEmits(["open-case"]);

const query = ref("");
const searched = ref(false);
const hit = ref(null);

function doSearch(q = query.value) {
  query.value = q;
  const key = q.trim();
  searched.value = !!key;
  hit.value =
    INTEL[key] ||
    Object.values(INTEL).find((x) => key && x.name.replaceAll(" ", "").includes(key.replaceAll(" ", ""))) ||
    null;
}

function createCase() {
  const c = CASES.find((x) => x.id === hit.value.id);
  if (c) emit("open-case", c);
  else alert("Demo:以此公司建立新授信案件");
}

// ---- 關係圖譜樣式 ----
const NODE_STYLE = {
  self:     { fill: "#0c4a6e", stroke: "#0c4a6e", text: "#ffffff" },
  supplier: { fill: "#fffbeb", stroke: "#d97706", text: "#92400e" },
  customer: { fill: "#ecfeff", stroke: "#0891b2", text: "#155e75" },
  related:  { fill: "#f8fafc", stroke: "#64748b", text: "#334155" },
};
const REL_STYLE = {
  supply: { stroke: "#94a3b8", dash: "", label: "供應" },
  board:  { stroke: "#d97706", dash: "5 4", label: "共同董監事" },
  patent: { stroke: "#0891b2", dash: "2 3", label: "專利引用" },
};
const nodeById = computed(() => Object.fromEntries((hit.value?.graph.nodes || []).map((n) => [n.id, n])));

const maxRev = computed(() => Math.max(...(hit.value?.revenue.map((r) => r.val) || [1])));
const SENTI = {
  pos: { label: "正面", cls: "bg-emerald-50 text-emerald-800 border-emerald-400" },
  neu: { label: "中性", cls: "bg-slate-100 text-slate-600 border-slate-300" },
  neg: { label: "負面", cls: "bg-rose-50 text-rose-800 border-rose-400" },
};
const srcTag = "inline-block px-1.5 py-0.5 rounded-sm text-xs bg-slate-100 text-slate-600 border border-slate-300";
</script>

<template>
  <main id="main" class="max-w-5xl mx-auto px-4 py-6 w-full">
    <nav aria-label="麵包屑" class="text-sm text-slate-500">
      <ol class="flex items-center gap-1 flex-wrap">
        <li>首頁</li>
        <li class="flex items-center gap-1"><span aria-hidden="true" class="text-slate-400 px-0.5">/</span><span aria-current="page" class="text-slate-700">情資查詢</span></li>
      </ol>
    </nav>

    <div class="mt-4">
      <h2 class="border-l-4 border-sky-800 pl-3 text-lg font-bold text-slate-900 mb-1">多源情資查詢</h2>
      <p class="text-sm text-slate-600 mb-3">介接 7 項公開資料源,輸入統一編號或公司名稱,檢視 AI 分析所依據的原始情資。</p>

      <form role="search" @submit.prevent="doSearch()" class="flex max-w-2xl">
        <label for="intel-search" class="sr-only">查詢公司</label>
        <input id="intel-search" type="search" v-model="query"
          placeholder="請輸入公司統一編號或名稱…" autocomplete="off" spellcheck="false"
          :class="`flex-1 h-11 px-4 text-slate-900 bg-white border border-slate-400 border-r-0 rounded-l-sm placeholder-slate-400 ${focusRing}`" />
        <button type="submit" :class="`h-11 px-6 bg-sky-900 hover:bg-sky-800 text-white font-bold rounded-r-sm motion-safe:transition-colors ${focusRing}`">
          查詢
        </button>
      </form>
      <p class="text-xs text-slate-500 mt-2">
        範例:
        <button @click="doSearch('12345678')"
          :class="`text-sky-800 hover:underline underline-offset-2 rounded-sm px-0.5 ${num} ${focusRing}`">12345678(XX 固態電池)</button>
      </p>
    </div>

    <!-- 查無資料 -->
    <div v-if="searched && !hit" class="mt-5 border border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
      尚未介接「{{ query.trim() }}」之外部情資,請確認統一編號或公司名稱。
    </div>

    <template v-if="hit">
      <!-- 公司抬頭 + 建立案件 -->
      <div class="mt-5 pb-3 border-b border-slate-300 flex items-end justify-between gap-4 flex-wrap">
        <div>
          <h3 class="text-xl font-bold text-slate-900">{{ hit.name }}</h3>
          <p :class="`text-sm text-slate-500 mt-1 ${num}`">統一編號 {{ hit.id }} · {{ hit.industry }} · {{ hit.reg.status }}</p>
        </div>
        <button @click="createCase"
          :class="`px-4 py-2 text-sm font-bold text-white bg-amber-600 hover:bg-amber-500 rounded-sm motion-safe:transition-colors ${focusRing}`">
          以此公司開啟授信案件 →
        </button>
      </div>

      <!-- 企業關係圖譜(GraphRAG 記憶點) -->
      <div class="mt-4 bg-white border border-slate-300 border-t-4 border-t-sky-900 p-4">
        <div class="flex items-baseline justify-between flex-wrap gap-2 mb-1">
          <h3 class="font-bold text-slate-900">企業關係圖譜</h3>
          <span :class="srcTag">資料來源:EAP 知識圖譜(統一編號為節點)</span>
        </div>
        <svg viewBox="0 0 640 360" class="w-full" style="max-height: 360px" role="img" aria-label="企業關係圖譜">
          <!-- 邊 -->
          <g v-for="(e, i) in hit.graph.edges" :key="'e' + i">
            <line :x1="nodeById[e.from].x" :y1="nodeById[e.from].y" :x2="nodeById[e.to].x" :y2="nodeById[e.to].y"
              :stroke="REL_STYLE[e.rel].stroke" stroke-width="1.5" :stroke-dasharray="REL_STYLE[e.rel].dash" />
            <text :x="(nodeById[e.from].x + nodeById[e.to].x) / 2" :y="(nodeById[e.from].y + nodeById[e.to].y) / 2 - 5"
              text-anchor="middle" font-size="10" :fill="REL_STYLE[e.rel].stroke">{{ REL_STYLE[e.rel].label }}</text>
          </g>
          <!-- 節點 -->
          <g v-for="n in hit.graph.nodes" :key="n.id">
            <rect :x="n.x - 62" :y="n.y - 20" width="124" height="40" rx="3"
              :fill="NODE_STYLE[n.type].fill" :stroke="n.warn ? '#e11d48' : NODE_STYLE[n.type].stroke"
              :stroke-width="n.warn ? 2.5 : n.type === 'self' ? 2 : 1.5" />
            <text :x="n.x" :y="n.y - 2" text-anchor="middle" font-size="12" font-weight="700" :fill="NODE_STYLE[n.type].text">{{ n.label }}</text>
            <text :x="n.x" :y="n.y + 13" text-anchor="middle" font-size="9" :fill="n.type === 'self' ? '#bae6fd' : '#94a3b8'" :class="num">{{ n.id }}</text>
            <text v-if="n.warn" :x="n.x" :y="n.y - 28" text-anchor="middle" font-size="10" font-weight="700" fill="#e11d48">⚠ 財務惡化警示</text>
          </g>
        </svg>
        <div class="flex justify-center gap-5 text-xs text-slate-600 flex-wrap">
          <span class="flex items-center gap-1.5"><span class="inline-block w-3 h-3 rounded-sm border-2" style="border-color:#d97706;background:#fffbeb" />上游供應商</span>
          <span class="flex items-center gap-1.5"><span class="inline-block w-3 h-3 rounded-sm border-2" style="border-color:#0891b2;background:#ecfeff" />下游客戶</span>
          <span class="flex items-center gap-1.5"><span class="inline-block w-3 h-3 rounded-sm border-2" style="border-color:#64748b;background:#f8fafc" />關係企業</span>
          <span class="flex items-center gap-1.5"><span class="inline-block w-4 border-t-2 border-dashed" style="border-color:#d97706" />共同董監事</span>
          <span class="flex items-center gap-1.5"><span class="inline-block w-4 border-t-2 border-dotted" style="border-color:#0891b2" />專利引用</span>
        </div>
        <div class="mt-3 border border-rose-300 border-l-4 border-l-rose-600 bg-rose-50 p-3 text-sm text-slate-800 leading-relaxed">
          <span class="font-bold text-rose-800">圖譜推理:</span>{{ hit.graph.alert }}
        </div>
      </div>

      <!-- 各資料源區塊 -->
      <div class="mt-4 grid lg:grid-cols-2 gap-4">
        <!-- 商工登記 -->
        <div class="bg-white border border-slate-300 p-4">
          <div class="flex items-baseline justify-between flex-wrap gap-2 mb-2">
            <h3 class="text-sm font-bold text-slate-900 border-l-4 border-sky-800 pl-2">公司登記資料</h3>
            <span :class="srcTag">資料來源:經濟部商工登記(data.gov.tw)</span>
          </div>
          <dl class="text-sm space-y-1.5">
            <div class="flex gap-2"><dt class="w-20 shrink-0 text-slate-500">資本額</dt><dd :class="`text-slate-800 ${num}`">{{ hit.reg.capital }}</dd></div>
            <div class="flex gap-2"><dt class="w-20 shrink-0 text-slate-500">設立日期</dt><dd :class="`text-slate-800 ${num}`">{{ hit.reg.founded }}</dd></div>
            <div class="flex gap-2"><dt class="w-20 shrink-0 text-slate-500">代表人</dt><dd class="text-slate-800">{{ hit.reg.chairman }}</dd></div>
            <div class="flex gap-2"><dt class="w-20 shrink-0 text-slate-500">登記地址</dt><dd class="text-slate-800">{{ hit.reg.address }}</dd></div>
            <div class="flex gap-2"><dt class="w-20 shrink-0 text-slate-500">董監事</dt>
              <dd class="text-slate-800 flex flex-wrap gap-1">
                <span v-for="d in hit.reg.directors" :key="d" class="px-1.5 py-0.5 bg-slate-100 border border-slate-300 rounded-sm text-xs">{{ d }}</span>
              </dd></div>
          </dl>
        </div>

        <!-- TWSE 月營收 -->
        <div class="bg-white border border-slate-300 p-4">
          <div class="flex items-baseline justify-between flex-wrap gap-2 mb-2">
            <h3 class="text-sm font-bold text-slate-900 border-l-4 border-sky-800 pl-2">近六個月營收(億元)</h3>
            <span :class="srcTag">資料來源:TWSE OpenAPI</span>
          </div>
          <div class="flex items-end gap-2 h-32 pt-2" role="img" aria-label="近六個月營收長條圖">
            <div v-for="r in hit.revenue" :key="r.m" class="flex-1 flex flex-col items-center gap-1 min-w-0">
              <span :class="`text-xs text-slate-700 ${num}`">{{ r.val }}</span>
              <div class="w-full bg-sky-800 rounded-t-sm" :style="{ height: `${(r.val / maxRev) * 80}px` }" />
              <span :class="`text-[10px] text-slate-500 ${num}`">{{ r.m.slice(4) }}</span>
              <span :class="`text-[10px] ${num} ${r.yoy >= 0 ? 'text-emerald-700' : 'text-rose-700'}`">{{ r.yoy >= 0 ? "+" : "" }}{{ r.yoy }}%</span>
            </div>
          </div>
        </div>

        <!-- 訴訟紀錄 -->
        <div class="bg-white border border-slate-300 p-4">
          <div class="flex items-baseline justify-between flex-wrap gap-2 mb-2">
            <h3 class="text-sm font-bold text-slate-900 border-l-4 border-sky-800 pl-2">訴訟紀錄({{ hit.lawsuits.length }} 件)</h3>
            <span :class="srcTag">資料來源:司法院裁判書開放 API</span>
          </div>
          <div v-if="hit.lawsuits.length === 0" class="text-sm text-slate-500">近五年無訴訟紀錄。</div>
          <div v-for="(l, i) in hit.lawsuits" :key="i" class="border border-slate-300 px-3 py-2 text-sm flex items-center gap-3 flex-wrap">
            <span :class="`${num} text-xs text-slate-500 shrink-0`">{{ l.date }}</span>
            <span :class="`${num} text-xs text-slate-600 shrink-0`">{{ l.no }}</span>
            <span class="text-slate-800 flex-1 min-w-32">{{ l.cause }}</span>
            <span class="text-xs px-1.5 py-0.5 border border-emerald-400 bg-emerald-50 text-emerald-800 rounded-sm shrink-0">{{ l.result }}</span>
          </div>
        </div>

        <!-- 裁罰紀錄 -->
        <div class="bg-white border border-slate-300 p-4">
          <div class="flex items-baseline justify-between flex-wrap gap-2 mb-2">
            <h3 class="text-sm font-bold text-slate-900 border-l-4 border-sky-800 pl-2">裁罰與違規紀錄({{ hit.fines.length }} 筆)</h3>
            <span :class="srcTag">資料來源:環境部/勞動部 Open Data</span>
          </div>
          <div v-if="hit.fines.length === 0" class="text-sm text-slate-500">查無裁罰紀錄。</div>
          <div v-for="(f, i) in hit.fines" :key="i" class="border border-slate-300 px-3 py-2 text-sm flex items-center gap-3 flex-wrap">
            <span :class="`${num} text-xs text-slate-500 shrink-0`">{{ f.date }}</span>
            <span class="text-xs px-1.5 py-0.5 border border-amber-400 bg-amber-50 text-amber-800 rounded-sm shrink-0">{{ f.agency }}</span>
            <span class="text-slate-800 flex-1 min-w-32">{{ f.law }} · 罰鍰 <span :class="num">{{ f.amount }}</span></span>
            <span class="text-xs px-1.5 py-0.5 border border-emerald-400 bg-emerald-50 text-emerald-800 rounded-sm shrink-0">{{ f.status }}</span>
          </div>
        </div>

        <!-- 專利 -->
        <div class="bg-white border border-slate-300 p-4">
          <div class="flex items-baseline justify-between flex-wrap gap-2 mb-2">
            <h3 class="text-sm font-bold text-slate-900 border-l-4 border-sky-800 pl-2">專利概況</h3>
            <span :class="srcTag">資料來源:TIPO 專利檢索</span>
          </div>
          <div class="flex gap-6 text-sm mb-3">
            <div><div class="text-xs text-slate-500">專利總數</div><div :class="`${num} font-bold text-xl text-sky-900`">{{ hit.patents.count }} 件</div></div>
            <div><div class="text-xs text-slate-500">被國際大廠引用</div><div :class="`${num} font-bold text-xl text-sky-900`">{{ hit.patents.cited }} 件</div></div>
          </div>
          <div class="text-xs text-slate-500 mb-1">近四年申請量趨勢</div>
          <div class="flex items-end gap-2 h-16">
            <div v-for="(v, i) in hit.patents.trend" :key="i" class="flex-1 flex flex-col items-center gap-0.5">
              <span :class="`text-[10px] text-slate-600 ${num}`">{{ v }}</span>
              <div class="w-full bg-cyan-700 rounded-t-sm" :style="{ height: `${(v / Math.max(...hit.patents.trend)) * 44}px` }" />
            </div>
          </div>
        </div>

        <!-- 新聞 -->
        <div class="bg-white border border-slate-300 p-4">
          <div class="flex items-baseline justify-between flex-wrap gap-2 mb-2">
            <h3 class="text-sm font-bold text-slate-900 border-l-4 border-sky-800 pl-2">近期新聞</h3>
            <span :class="srcTag">資料來源:GDELT 全球新聞事件庫</span>
          </div>
          <ul>
            <li v-for="(n, i) in hit.news" :key="i" class="border-b border-slate-200 last:border-0 py-2 flex items-center gap-3 text-sm flex-wrap">
              <span :class="`${num} text-xs text-slate-500 shrink-0`">{{ n.date }}</span>
              <span class="text-slate-800 flex-1 min-w-40">{{ n.title }}</span>
              <span :class="['text-xs px-1.5 py-0.5 border rounded-sm shrink-0', SENTI[n.senti].cls]">{{ SENTI[n.senti].label }}</span>
            </li>
          </ul>
        </div>
      </div>
    </template>
  </main>
</template>
