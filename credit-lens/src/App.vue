<script setup>
// ============================================================
// 智貸先鋒 企業授信情資服務網 — App 骨架
// 職責:上方工具列 / Header / Footer / 字級調整 / 頁面切換
// 頁面內容見 pages/,四個頁籤元件見 components/
// ============================================================
import { ref, computed } from "vue";
import { focusRing } from "./constants.js";
import DashboardPage from "./pages/DashboardPage.vue";
import CasePage from "./pages/CasePage.vue";
import IntelPage from "./pages/IntelPage.vue";
import ReportPage from "./pages/ReportPage.vue";

const page = ref("dashboard");
const current = ref(null);
const nav = ref("案件總覽");
const fontScale = ref("m");
const fontSize = computed(() => ({ s: "15px", m: "16px", l: "17.5px" }[fontScale.value]));
const fontSizes = [{ k: "s", label: "小" }, { k: "m", label: "中" }, { k: "l", label: "大" }];
const navItems = ["案件總覽", "情資查詢", "報告中心", "關於平臺"];
const NAV_PAGE = { "案件總覽": "dashboard", "情資查詢": "intel", "報告中心": "reports" };

function goHome() { page.value = "dashboard"; current.value = null; nav.value = "案件總覽"; }
function onNav(t) {
  if (!NAV_PAGE[t]) return; // 關於平臺:尚未實作,維持現頁
  nav.value = t; current.value = null; page.value = NAV_PAGE[t];
}
function openCase(c) { current.value = c; page.value = "case"; nav.value = "案件總覽"; }
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

    <div class="flex-1">
      <DashboardPage v-if="page === 'dashboard'" @open-case="openCase" />
      <IntelPage v-else-if="page === 'intel'" @open-case="openCase" />
      <ReportPage v-else-if="page === 'reports'" />
      <CasePage v-else :c="current" @go-home="goHome" />
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
/* 全域(不加 scoped):fadeUp 供各子元件的 motion-safe:animate-[fadeUp_...] 使用 */
@keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
button { touch-action: manipulation; }
</style>
