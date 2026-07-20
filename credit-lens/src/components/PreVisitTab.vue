<script setup>
// 頁籤 2:拜訪前情資(手刻 SVG 雷達圖 + 防禦提問單)
// 資料來源 = 規格書 5.7 /api/pre/brief 回應(目前為 Mock)
import { ref, computed } from "vue";
import { AGENT, num } from "../constants.js";
import { MOCK } from "../mock.js";

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
</script>

<template>
  <div class="space-y-5">
    <div class="grid lg:grid-cols-2 gap-4">
      <div class="bg-white border border-slate-300 p-3">
        <h3 class="text-sm font-bold text-slate-900 border-l-4 border-sky-800 pl-2 mb-1">護城河雷達圖</h3>
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
</template>
