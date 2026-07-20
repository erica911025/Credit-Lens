<script setup>
// 頁籤 1:AI 審查會議(phase 狀態機 7.1:idle/finance/tech/judge/done)
import { ref, reactive, computed, nextTick } from "vue";
import { AGENT, SEVERITY, focusRing, num } from "../constants.js";
import { reviewApi } from "../api.js";
import { MOCK } from "../mock.js";
import WaterfallChart from "./WaterfallChart.vue";

const props = defineProps({ c: { type: Object, required: true } });

const phase = ref("idle");
const r = reactive({ finance: null, tech: null, judge: null });
const err = ref(null);
const committeeEnd = ref(null);
const busy = computed(() => phase.value !== "idle" && phase.value !== "done");

function scrollToEnd() { nextTick(() => committeeEnd.value?.scrollIntoView({ behavior: "smooth", block: "nearest" })); }

// resume:7.3 已渲染卡片保留,重試從失敗的那一段開始
async function run(resume = false) {
  err.value = null;
  const req = { company_id: props.c.id, company_name: props.c.name }; // 5.3 Request
  if (!resume) { r.finance = null; r.tech = null; r.judge = null; }
  try {
    if (!r.finance) {
      phase.value = "finance"; scrollToEnd();
      r.finance = await reviewApi("/api/review/finance", req, MOCK.finance);   // 5.3
    }
    if (!r.tech) {
      phase.value = "tech"; scrollToEnd();
      r.tech = await reviewApi("/api/review/tech", req, MOCK.tech);            // 5.4
    }
    phase.value = "judge"; scrollToEnd();
    r.judge = await reviewApi("/api/review/judge",
      { company_id: props.c.id, finance_result: r.finance, tech_result: r.tech }, // 5.5:前兩支回應原封不動帶入
      MOCK.judge, 2000);
    phase.value = "done"; scrollToEnd();
  } catch (e) {
    err.value = e;        // 顯示 error.message + 重試按鈕(7.3)
    phase.value = "idle"; // phase 回到 idle(7.3)
    scrollToEnd();
  }
}
</script>

<template>
  <div class="space-y-3">
    <div class="bg-sky-50 border border-sky-200 px-4 py-3 flex items-center justify-between gap-4 flex-wrap">
      <p class="text-sm text-slate-700">由財務、技術兩位分析 Agent 發言,風險審查官交叉質詢後裁決基準分。</p>
      <button @click="run(false)" :disabled="busy"
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
      <button @click="run(true)"
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
      <WaterfallChart :items="r.judge.waterfall" :final-score="r.judge.final_score" />
    </div>
    <div ref="committeeEnd" />
  </div>
</template>
