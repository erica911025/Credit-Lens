<script setup>
// 頁面 1:案件總覽(Hero 搜尋 + 進行中案件列表 + 最新公告)
import { ref, computed } from "vue";
import { STAGE_LABEL, focusRing, num } from "../constants.js";
import { CASES, ANNOUNCEMENTS } from "../mock.js";

const emit = defineEmits(["open-case"]);

const query = ref("");
const caseList = computed(() => {
  const q = query.value.trim();
  return CASES.filter((c) => !q || c.name.includes(q) || c.id.includes(q));
});
</script>

<template>
  <div>
    <!-- Hero 色帶:標語 + 大搜尋框 + 統計數字(data.taipei 式) -->
    <div class="bg-sky-900 text-white">
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

    <main id="main" class="max-w-5xl mx-auto px-4 py-6 w-full">
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
            <button @click="emit('open-case', c)"
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
          <li v-for="([d, tg, t], i) in ANNOUNCEMENTS" :key="i" class="border-b border-slate-300 bg-white px-4 py-3 flex items-center gap-3 text-sm flex-wrap">
            <span :class="`${num} text-xs text-slate-500 w-24 shrink-0`">{{ d }}</span>
            <span class="text-xs px-1.5 py-0.5 border border-amber-400 bg-amber-50 text-amber-800 rounded-sm shrink-0">{{ tg }}</span>
            <a href="#" @click.prevent :class="`text-slate-800 hover:text-sky-900 hover:underline underline-offset-2 rounded-sm ${focusRing}`">{{ t }}</a>
          </li>
        </ul>
      </div>
    </main>
  </div>
</template>
