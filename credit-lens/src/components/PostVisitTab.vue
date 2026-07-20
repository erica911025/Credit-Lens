<script setup>
// 頁籤 4:拜訪後評分
// 資料來源 = 規格書 5.9 /api/postvisit/extract、5.10 /api/postvisit/score、5.6 /api/report
import { ref, computed } from "vue";
import { VERDICT, focusRing, num } from "../constants.js";
import { reviewApi, USE_MOCK, API_BASE } from "../api.js";
import { MOCK, SAMPLE_NOTES } from "../mock.js";
import { store } from "../store.js";
import WaterfallChart from "./WaterfallChart.vue";

const props = defineProps({ c: { type: Object, required: true } });

const notes = ref(SAMPLE_NOTES);
const stage = ref("idle");
const ext = ref(null);
const sc = ref(null);
const busy = computed(() => stage.value === "extracting" || stage.value === "scoring");

const runErr = ref(null);

async function run() {
  ext.value = null; sc.value = null; runErr.value = null; stage.value = "extracting";
  try {
    // 5.9:會議紀錄結構化萃取
    ext.value = await reviewApi("/api/postvisit/extract",
      { company_id: props.c.id, notes: notes.value }, MOCK.postExtract, 1700);
    stage.value = "scoring";
    // 5.10:base_score = AI 審查會議產出的拜訪前基準分(store);未召開過會議時退回 Mock 的 71
    const baseScore = store.judgeByCompany[props.c.id]?.final_score ?? MOCK.judge.final_score;
    sc.value = await reviewApi("/api/postvisit/score",
      { company_id: props.c.id, base_score: baseScore, extract_result: ext.value }, MOCK.postScore, 1500);
    stage.value = "done";
  } catch (e) {
    runErr.value = e; stage.value = "idle"; // 7.3:顯示 error.message + 重試
  }
}

// 5.6:產出授信審查報告 PDF → 新分頁開啟 report_url
const reporting = ref(false);
async function makeReport() {
  if (USE_MOCK) { alert("Demo(USE_MOCK):整合日將呼叫 POST /api/report 並開啟 PDF"); return; }
  const judge = store.judgeByCompany[props.c.id];
  if (!judge) { alert("請先於「AI 審查會議」頁籤完成審查,才能產出報告(需要 judge_result)。"); return; }
  reporting.value = true;
  try {
    const r = await reviewApi("/api/report", { company_id: props.c.id, judge_result: judge }, { report_url: "" });
    if (r.report_url) window.open(new URL(r.report_url, API_BASE).href, "_blank");
  } catch (e) {
    alert(`報告產出失敗(${e.code}):${e.message}`);
  }
  reporting.value = false;
}
</script>

<template>
  <div class="space-y-4">
    <div class="bg-white border border-slate-300 p-4">
      <label for="notes" class="block text-sm font-bold text-slate-900 mb-2">
        會議紀錄<span class="ml-2 text-xs font-normal text-slate-500">貼上自由格式紀錄,AI 自動結構化萃取</span>
      </label>
      <textarea id="notes" v-model="notes" rows="7" spellcheck="false"
        :class="`w-full border border-slate-300 p-3 text-sm leading-relaxed text-slate-800 resize-none rounded-sm bg-slate-50 focus:bg-white focus:border-sky-700 ${focusRing}`" />
      <button @click="run" :disabled="busy || !notes.trim()"
        :class="`mt-2.5 px-6 h-10 text-sm font-bold text-white bg-sky-900 hover:bg-sky-800 disabled:bg-slate-300 disabled:text-slate-500 rounded-sm motion-safe:transition-colors ${focusRing}`">
        {{ busy ? "分析中…" : "開始分析" }}
      </button>
    </div>

    <div v-if="runErr" role="alert" class="border border-rose-300 border-l-4 border-l-rose-600 bg-rose-50 p-4 flex items-center justify-between gap-4 flex-wrap">
      <div>
        <div class="font-bold text-rose-800 text-sm mb-0.5">分析中斷({{ runErr.code }})</div>
        <p class="text-sm text-slate-800 leading-relaxed">{{ runErr.message }}</p>
      </div>
      <button @click="run" class="px-5 h-10 text-sm font-bold text-white bg-rose-700 hover:bg-rose-600 rounded-sm motion-safe:transition-colors">重試</button>
    </div>

    <div v-if="stage === 'extracting'" class="bg-white border border-slate-300 p-4 text-sm text-slate-500" aria-live="polite">
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

      <div v-if="ext.new_risks.length > 0">
        <div class="text-xs font-bold text-rose-800 mb-1.5">三、面談中新發現的風險</div>
        <div v-for="(n, i) in ext.new_risks" :key="i"
          class="border border-rose-300 border-l-4 border-l-rose-600 bg-rose-50 p-3 text-sm text-slate-800 leading-relaxed">{{ n.text }}</div>
      </div>
    </div>

    <div v-if="stage === 'scoring'" class="bg-white border border-slate-300 p-4 text-sm text-slate-500" aria-live="polite">
      比對拜訪前基準,計算增減項<span class="animate-pulse" aria-hidden="true"> …</span>
    </div>

    <div v-if="sc" class="bg-white border border-slate-300 border-t-4 border-t-emerald-600 p-4 motion-safe:animate-[fadeUp_.4s_ease-out]">
      <h3 class="font-bold text-slate-900 mb-3">評分瀑布 — 每一分的來源</h3>
      <WaterfallChart :items="sc.waterfall" :final-score="sc.final_score" />
      <div class="mt-4 bg-slate-50 border border-slate-300 p-3 text-sm leading-relaxed">
        <span class="font-bold text-sky-900">審查官建議:</span>
        <span class="text-slate-800"> {{ sc.recommendation }}</span>
      </div>
      <button @click="makeReport"
        :class="`mt-3 px-6 h-11 text-sm font-bold text-white bg-emerald-700 hover:bg-emerald-600 rounded-sm motion-safe:transition-colors ${focusRing}`">
        {{ reporting ? "報告產出中…" : "產出授信審查報告(PDF)" }}
      </button>
    </div>
  </div>
</template>
