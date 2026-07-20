// 跨頁籤共用狀態:AI 審查會議的裁決結果
// 「拜訪後評分」需要 base_score(5.10)、「產出報告」需要 judge_result(5.6)
import { reactive } from "vue";

export const store = reactive({
  judgeByCompany: {}, // { [company_id]: JudgeResult }
});
