<script setup>
// 頁面 4:報告中心(報告歸檔 + 跨案件承諾事項追蹤)
// 報告列表 = 5.6 /api/report 產出物的歸宿;承諾追蹤 = 5.9 extract 之 commitments 彙總
import { ref, computed } from "vue";
import { focusRing, num } from "../constants.js";
import { REPORTS, TRACKED_COMMITMENTS } from "../mock.js";

// 今日(民國):與 Demo 劇本一致
const TODAY = "115-07-20";
const toDate = (roc) => { const [y, m, d] = roc.split("-").map(Number); return new Date(1911 + y, m - 1, d); };
const daysLeft = (due) => Math.round((toDate(due) - toDate(TODAY)) / 86400000);

const STATUS = {
  "已核定": "bg-emerald-50 text-emerald-800 border-emerald-400",
  "已送審": "bg-sky-50 text-sky-800 border-sky-400",
  "草稿":   "bg-slate-100 text-slate-600 border-slate-300",
};

const filter = ref("全部");
const filterOptions = ["全部", "草稿", "已送審", "已核定"];
const reportList = computed(() => REPORTS.filter((r) => filter.value === "全部" || r.status === filter.value));

const commitments = computed(() =>
  TRACKED_COMMITMENTS.map((c) => ({ ...c, left: daysLeft(c.due) })).sort((a, b) => a.left - b.left)
);
const overdueCount = computed(() => commitments.value.filter((c) => c.left < 0).length);

const stats = computed(() => [
  ["本月產出報告", `${REPORTS.length} 份`],
  ["平均綜合評分", `${Math.round(REPORTS.reduce((a, r) => a + r.score, 0) / REPORTS.length)} 分`],
  ["追蹤中承諾事項", `${TRACKED_COMMITMENTS.length} 項`],
]);

// 5.6:整合時改為開啟後端回傳之 report_url
function download(r) { alert(`Demo:下載 ${r.company}【${r.version}】PDF`); }
</script>

<template>
  <main id="main" class="max-w-5xl mx-auto px-4 py-6 w-full">
    <nav aria-label="麵包屑" class="text-sm text-slate-500">
      <ol class="flex items-center gap-1 flex-wrap">
        <li>首頁</li>
        <li class="flex items-center gap-1"><span aria-hidden="true" class="text-slate-400 px-0.5">/</span><span aria-current="page" class="text-slate-700">報告中心</span></li>
      </ol>
    </nav>

    <!-- 統計小卡 -->
    <div class="mt-4 grid sm:grid-cols-3 gap-3">
      <div v-for="[k, v] in stats" :key="k" class="bg-white border border-slate-300 border-t-4 border-t-sky-900 px-4 py-3">
        <div class="text-xs text-slate-500">{{ k }}</div>
        <div :class="`${num} font-bold text-2xl text-sky-900 mt-0.5`">{{ v }}</div>
      </div>
    </div>

    <!-- 報告列表 -->
    <div class="mt-6">
      <div class="flex items-center justify-between gap-4 mb-3 flex-wrap">
        <h2 class="border-l-4 border-sky-800 pl-3 text-lg font-bold text-slate-900">授信審查報告</h2>
        <div class="flex items-center gap-2 text-sm">
          <label for="rep-filter" class="text-slate-600">狀態</label>
          <select id="rep-filter" v-model="filter"
            :class="`h-9 px-2 border border-slate-400 rounded-sm bg-white text-slate-800 ${focusRing}`">
            <option v-for="o in filterOptions" :key="o" :value="o">{{ o }}</option>
          </select>
        </div>
      </div>

      <div v-if="reportList.length === 0" class="border border-slate-300 bg-white p-10 text-center text-sm text-slate-500">
        無符合條件的報告。
      </div>
      <ul v-else class="border-t-2 border-sky-900">
        <li v-for="(r, i) in reportList" :key="i"
          class="border-b border-slate-300 bg-white px-4 py-3 flex items-center gap-4 flex-wrap hover:bg-sky-50 motion-safe:transition-colors">
          <span :class="`${num} text-xs text-slate-500 w-24 shrink-0`">{{ r.date }}</span>
          <span class="flex-1 min-w-48">
            <span class="text-slate-900 font-medium">{{ r.company }}</span>
            <span :class="`block text-xs text-slate-500 mt-0.5 ${num}`">統一編號 {{ r.id }}</span>
          </span>
          <span class="text-xs px-1.5 py-0.5 border border-sky-300 bg-sky-50 text-sky-900 rounded-sm shrink-0">{{ r.version }}</span>
          <span class="w-14 text-right shrink-0">
            <span :class="`${num} font-bold text-lg text-sky-900`">{{ r.score }}</span><span class="text-xs text-slate-500"> 分</span>
          </span>
          <span :class="['text-xs px-1.5 py-0.5 border rounded-sm shrink-0', STATUS[r.status]]">{{ r.status }}</span>
          <button @click="download(r)"
            :class="`px-3 h-9 text-xs font-bold text-white bg-sky-900 hover:bg-sky-800 rounded-sm shrink-0 motion-safe:transition-colors ${focusRing}`">
            下載 PDF
          </button>
        </li>
      </ul>
    </div>

    <!-- 承諾事項追蹤 -->
    <div class="mt-8">
      <div class="flex items-center justify-between gap-4 mb-3 flex-wrap">
        <h2 class="border-l-4 border-sky-800 pl-3 text-lg font-bold text-slate-900">承諾事項追蹤</h2>
        <span v-if="overdueCount > 0" class="text-xs px-2 py-1 border border-rose-400 bg-rose-50 text-rose-800 rounded-sm font-bold">
          {{ overdueCount }} 項已逾期
        </span>
      </div>
      <p class="text-xs text-slate-500 mb-2">由「拜訪後評分」之會議紀錄萃取自動列入;基準日 {{ TODAY }}。</p>

      <table class="w-full text-sm border-collapse bg-white">
        <thead>
          <tr class="bg-slate-100 text-slate-700 text-xs">
            <th scope="col" class="border border-slate-300 px-2 py-1.5 text-left font-bold w-28">案件</th>
            <th scope="col" class="border border-slate-300 px-2 py-1.5 text-left font-bold">承諾內容</th>
            <th scope="col" class="border border-slate-300 px-2 py-1.5 text-left font-bold w-28">承諾人</th>
            <th scope="col" class="border border-slate-300 px-2 py-1.5 text-left font-bold w-24">期限</th>
            <th scope="col" class="border border-slate-300 px-2 py-1.5 text-right font-bold w-24">剩餘天數</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(c, i) in commitments" :key="i" :class="c.left < 0 ? 'bg-rose-50' : 'hover:bg-sky-50'">
            <td class="border border-slate-300 px-2 py-1.5 text-slate-600">{{ c.company }}</td>
            <td class="border border-slate-300 px-2 py-1.5 text-slate-800">
              {{ c.item }}
              <span v-if="c.left < 0" class="ml-1.5 text-xs px-1.5 py-0.5 border border-rose-400 bg-white text-rose-800 rounded-sm font-bold">逾期</span>
            </td>
            <td class="border border-slate-300 px-2 py-1.5 text-slate-600">{{ c.owner }}</td>
            <td :class="`border border-slate-300 px-2 py-1.5 ${num} ${c.left < 0 ? 'text-rose-800 font-bold' : 'text-slate-800'}`">{{ c.due }}</td>
            <td :class="`border border-slate-300 px-2 py-1.5 text-right ${num} font-bold ${c.left < 0 ? 'text-rose-700' : c.left <= 7 ? 'text-amber-700' : 'text-emerald-700'}`">
              {{ c.left < 0 ? `逾期 ${-c.left} 天` : `${c.left} 天` }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>
