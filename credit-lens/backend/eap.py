# eap.py — 精誠 EAP 封裝(規格書 3.2 / 7.3)
# 真實流程(由組員實測破解,GeminiData 平台 v1 路由):
#   階段 1:POST {EAP_API_URL}                body={"name": "..."}    → 取得聊天室 id
#   階段 2:POST {EAP_API_URL}/{id}/messages  body={"message": "..."} → 回應欄位 reply
# 本模組職責:兩階段呼叫、逾時、失敗重試 1 次、LLM 回傳非法 JSON 時修復
import os
import json
import re
from pathlib import Path

import httpx

PROMPT_DIR = Path(__file__).parent / "prompts"


class EapError(Exception):
    def __init__(self, code: str, status: int, message: str):
        self.code, self.status, self.message = code, status, message


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / f"{name}.txt").read_text(encoding="utf-8")


def repair_json(text: str) -> dict:
    """LLM 回傳非法 JSON 時的修復(7.3):去除 markdown 圍欄、擷取最外層大括號。"""
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(t[start : end + 1])
        except json.JSONDecodeError:
            pass
    raise EapError("LLM_FORMAT_ERROR", 502, "LLM 回傳格式無法修復,請重試")


def _headers() -> dict:
    token = os.getenv("EAP_TOKEN", "")
    if not token:
        raise EapError("INTERNAL_ERROR", 500, "後端未設定 EAP_TOKEN,請檢查 .env")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def _chat_once(client: httpx.AsyncClient, system_prompt: str, user_message: str, session_name: str) -> str:
    """執行一次完整的兩階段呼叫,回傳模型文字。"""
    base = os.getenv("EAP_API_URL", "https://cloud.geminidata.com/api/v1/chats")

    # 階段 1:初始化聊天室(帶 name 防 405;每次開新聊天室,避免歷史訊息污染判定)
    r1 = await client.post(base, json={"name": session_name}, headers=_headers())
    if r1.status_code == 401:
        raise EapError("INTERNAL_ERROR", 500, "EAP Token 無效或過期,請更新 .env 之 EAP_TOKEN")
    r1.raise_for_status()
    chat_id = r1.json().get("id")
    if not chat_id:
        raise EapError("LLM_FORMAT_ERROR", 502, "EAP 初始化聊天室未回傳 id")

    # 階段 2:送入 System Prompt + 任務訊息
    r2 = await client.post(
        f"{base}/{chat_id}/messages",
        json={"message": f"{system_prompt}\n\n---\n\n{user_message}"},
        headers=_headers(),
    )
    r2.raise_for_status()
    reply = r2.json().get("reply") or ""
    if not reply or "無法初始化聊天室" in reply:
        raise EapError("LLM_FORMAT_ERROR", 502, "EAP 回覆為空或初始化失敗")
    return reply


async def call_chat(system_prompt: str, user_message: str, session_name: str = "Credit-Lens 審查") -> dict:
    """呼叫 EAP,回傳解析後的 JSON dict。逾時 60 秒、失敗自動重試 1 次(7.3)。"""
    last_err: EapError | None = None
    for _ in range(2):  # 首次 + 重試 1 次
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=15.0)) as client:
                reply = await _chat_once(client, system_prompt, user_message, session_name)
                return repair_json(reply)
        except httpx.TimeoutException:
            last_err = EapError("EAP_TIMEOUT", 504, "EAP 平台回應逾時,請重試")
        except httpx.HTTPError:
            last_err = EapError("EAP_TIMEOUT", 504, "EAP 平台呼叫失敗,請重試")
        except EapError as e:
            last_err = e
    raise last_err


async def ask_agent(agent: str, user_message: str, session_name: str = "Credit-Lens 審查") -> dict:
    """agent = prompts/ 下的檔名(finance/tech/judge/pre_brief/assess/extract/score)"""
    return await call_chat(load_prompt(agent), user_message, session_name)
