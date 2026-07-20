<script setup>
// 頁面 2:案件詳情(四個工作流頁籤容器)
import { ref } from "vue";
import { TABS, focusRing, num } from "../constants.js";
import CommitteeTab from "../components/CommitteeTab.vue";
import PreVisitTab from "../components/PreVisitTab.vue";
import MidVisitTab from "../components/MidVisitTab.vue";
import PostVisitTab from "../components/PostVisitTab.vue";

const props = defineProps({ c: { type: Object, required: true } });
const emit = defineEmits(["go-home"]);

const tab = ref("committee");
</script>

<template>
  <main id="main" class="max-w-5xl mx-auto px-4 py-5 w-full">
    <nav aria-label="麵包屑" class="text-sm text-slate-500">
      <ol class="flex items-center gap-1 flex-wrap">
        <li><button @click="emit('go-home')" :class="`text-sky-800 hover:underline underline-offset-2 rounded-sm px-0.5 ${focusRing}`">首頁</button></li>
        <li class="flex items-center gap-1"><span aria-hidden="true" class="text-slate-400 px-0.5">/</span>
          <button @click="emit('go-home')" :class="`text-sky-800 hover:underline underline-offset-2 rounded-sm px-0.5 ${focusRing}`">案件總覽</button></li>
        <li class="flex items-center gap-1"><span aria-hidden="true" class="text-slate-400 px-0.5">/</span><span aria-current="page" class="text-slate-700">{{ c.name }}</span></li>
      </ol>
    </nav>

    <div class="mt-4 mb-4 pb-3 border-b border-slate-300 flex items-end justify-between gap-4 flex-wrap">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">{{ c.name }}</h1>
        <p :class="`text-sm text-slate-500 mt-1 ${num}`">統一編號 {{ c.id }} · {{ c.industry }} · 最近更新 {{ c.updated }}</p>
      </div>
      <div v-if="c.score !== null" class="text-right">
        <div class="text-xs text-slate-500">目前綜合評分</div>
        <span :class="`${num} font-bold text-3xl text-sky-900`">{{ c.score }}<span class="text-xs text-slate-500 font-normal"> 分</span></span>
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
      <CommitteeTab v-if="tab === 'committee'" :c="c" />
      <PreVisitTab v-else-if="tab === 'pre'" />
      <MidVisitTab v-else-if="tab === 'mid'" />
      <PostVisitTab v-else-if="tab === 'post'" />
    </div>
  </main>
</template>
