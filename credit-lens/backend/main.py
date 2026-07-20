# main.py — Credit-Lens FastAPI 後端(規格書 v1.1 第 5 章全部 API + 情資/報告中心三支)
# 執行:uvicorn main:app --reload --port 8000
# MOCK_MODE=true(.env)時所有 API 回傳規格書範例 JSON(Demo 保險絲,7.3)
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import mock_data as MOCK
import models as M
from eap import EapError, ask_agent

load_dotenv()
MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"
# 展示防禦(組員版構想的誠實化):EAP 呼叫失敗時自動降級回規格書範例 JSON,
# Demo 現場網路/平台出狀況也不會中斷;設 false 則回傳 5.2 錯誤格式讓前端顯示重試。
FALLBACK_ON_ERROR = os.getenv("FALLBACK_ON_ERROR", "true").lower() == "true"
REPORT_DIR = Path(__file__).parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Credit-Lens API", version="1.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("ALLOW_ORIGINS", "*").split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/reports", StaticFiles(directory=REPORT_DIR), name="reports")


# ---------- 統一錯誤格式(5.2) ----------
def err(status: int, code: str, message: str):
    raise HTTPException(status_code=status, detail={"code": code, "message": message})


@app.exception_handler(HTTPException)
async def http_exc_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "INTERNAL_ERROR", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": detail})


@app.exception_handler(Exception)
async def any_exc_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "系統發生未預期錯誤"}})


async def eap_or_fallback(agent: str, message: str, fallback: dict, session_name: str) -> dict:
    """呼叫 EAP;失敗時依 FALLBACK_ON_ERROR 決定降級回範例 JSON 或回傳錯誤(7.3 展示保險絲)。"""
    try:
        return await ask_agent(agent, message, session_name)
    except EapError as e:
        if FALLBACK_ON_ERROR:
            print(f"⚠️ [展示防禦] EAP 呼叫失敗({e.code}: {e.message}),自動降級回範例資料。")
            return dict(fallback)
        err(e.status, e.code, e.message)


# ---------- 共用驗證 ----------
def drop_no_cite(findings: list[dict]) -> list[dict]:
    """防幻覺(10.1):無 cite 的發現直接丟棄。"""
    return [f for f in findings if f.get("cite")]


def fix_waterfall(waterfall: list[dict], base_value: int | None = None) -> tuple[list[dict], int]:
    """數學一致(5.5/5.10):基礎分 + 各增減項 = final_score,由後端驗算保證。
    base_value 給定時(5.10)強制第一筆 type=base 且 value=base_value。"""
    if not waterfall or waterfall[0].get("type") != "base":
        err(502, "LLM_FORMAT_ERROR", "waterfall 第一筆必須為 base")
    if base_value is not None:
        waterfall[0]["value"] = base_value
    total = waterfall[0]["value"] + sum(w["value"] for w in waterfall[1:])
    return waterfall, max(0, min(100, total))


# ---------- 5.3 財務分析 Agent ----------
@app.post("/api/review/finance", response_model=M.AgentResult)
async def review_finance(req: M.ReviewRequest):
    if MOCK_MODE:
        return MOCK.FINANCE
    data = await eap_or_fallback(
        "finance",
        f"目標企業:{req.company_name}(統一編號 {req.company_id})。請依 EAP 知識庫中該企業之財報與信用資料進行分析。",
        MOCK.FINANCE, f"財務審查-{req.company_name or req.company_id}")
    if data.get("error") == "INSUFFICIENT_DATA":
        err(404, "COMPANY_NOT_FOUND", "查無此公司資料")
    data["agent"] = "finance"
    data["findings"] = drop_no_cite(data.get("findings", []))
    return M.AgentResult(**data)


# ---------- 5.4 技術情報 Agent ----------
@app.post("/api/review/tech", response_model=M.AgentResult)
async def review_tech(req: M.ReviewRequest):
    if MOCK_MODE:
        return MOCK.TECH
    data = await eap_or_fallback(
        "tech",
        f"目標企業:{req.company_name}(統一編號 {req.company_id})。請依 EAP 知識庫中該企業之專利、研報、新聞資料評估技術護城河。",
        MOCK.TECH, f"技術審查-{req.company_name or req.company_id}")
    if data.get("error") == "INSUFFICIENT_DATA":
        err(404, "COMPANY_NOT_FOUND", "查無此公司資料")
    data["agent"] = "tech"
    data["findings"] = drop_no_cite(data.get("findings", []))
    return M.AgentResult(**data)


# ---------- 5.5 風險審查官 ----------
@app.post("/api/review/judge", response_model=M.JudgeResult)
async def review_judge(req: M.JudgeRequest):
    if MOCK_MODE:
        return MOCK.JUDGE
    payload = json.dumps(
        {"finance_result": req.finance_result.model_dump(), "tech_result": req.tech_result.model_dump()},
        ensure_ascii=False,
    )
    data = await eap_or_fallback(
        "judge", f"以下是財務與技術兩位 Agent 的完整報告,請交叉質詢並裁決:\n{payload}",
        MOCK.JUDGE, f"交叉質詢-{req.company_id}")
    data["agent"] = "judge"
    data["waterfall"], data["final_score"] = fix_waterfall(data.get("waterfall", []))
    return M.JudgeResult(**data)


# ---------- 5.6 產出授信審查報告 PDF ----------
@app.post("/api/report", response_model=M.ReportResult)
async def make_report(req: M.ReportRequest):
    filename = f"{req.company_id}_{datetime.now():%Y%m%d%H%M%S}.pdf"
    _render_pdf(REPORT_DIR / filename, req)
    return {"report_url": f"/reports/{filename}"}


def _render_pdf(path: Path, req: M.ReportRequest):
    """以 reportlab 產出簡版授信審查報告。
    優先內嵌 fonts/NotoSansTC-Regular.ttf(所有讀者可開);找不到才退回 CID 字型。"""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfgen import canvas

    font_file = Path(__file__).parent / "fonts" / "NotoSansTC-Regular.ttf"
    if font_file.exists():
        from reportlab.pdfbase.ttfonts import TTFont

        if "NotoTC" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("NotoTC", str(font_file)))
        font_name = "NotoTC"
    else:  # 備援:Adobe CID(部分閱讀器需語言包)
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont

        if "MSung-Light" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
        font_name = "MSung-Light"

    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    y = h - 60

    def line(text, size=11, dy=20, bold_bar=False):
        nonlocal y
        if bold_bar:
            c.setFillColorRGB(0.05, 0.29, 0.43)
            c.rect(50, y - 3, 3, 12, fill=1, stroke=0)
            c.setFillColorRGB(0, 0, 0)
            c.setFont(font_name, size)
            c.drawString(58, y, text)
        else:
            c.setFont(font_name, size)
            c.drawString(50, y, text)
        y -= dy

    j = req.judge_result
    line("智貸先鋒 Credit-Lens 授信審查報告", 16, 28)
    line(f"統一編號:{req.company_id}    產出時間:{datetime.now():%Y-%m-%d %H:%M}", 10, 24)
    line(f"綜合評分:{j.final_score} 分", 13, 24, bold_bar=True)
    line("評分瀑布:", 11, 18, bold_bar=True)
    for wtr in j.waterfall:
        sign = "" if wtr.type == "base" else ("+" if wtr.value > 0 else "")
        line(f"  {wtr.label}:{sign}{wtr.value}", 10, 16)
    line("矛盾點:", 11, 18, bold_bar=True)
    if not j.contradictions:
        line("  無重大矛盾", 10, 16)
    for x in j.contradictions:
        line(f"  [{x.severity}] {x.title} — {x.detail}", 10, 16)
    line("裁決:", 11, 18, bold_bar=True)
    for chunk in [j.verdict[i : i + 42] for i in range(0, len(j.verdict), 42)]:
        line(f"  {chunk}", 10, 16)
    c.showPage()
    c.save()


# ---------- 5.7 拜訪前情資 ----------
@app.post("/api/pre/brief", response_model=M.BriefResult)
async def pre_brief(req: M.ReviewRequest):
    if MOCK_MODE:
        return MOCK.BRIEF
    data = await eap_or_fallback(
        "pre_brief",
        f"目標企業:{req.company_name}(統一編號 {req.company_id})。請依 EAP 知識庫產出六維雷達與防禦提問單。",
        MOCK.BRIEF, f"拜訪前情資-{req.company_name or req.company_id}")
    if data.get("error") == "INSUFFICIENT_DATA":
        err(404, "COMPANY_NOT_FOUND", "查無此公司資料")
    return M.BriefResult(**data)


# ---------- 5.8 拜訪中即時判定 ----------
@app.post("/api/interview/assess", response_model=M.AssessResult)
async def interview_assess(req: M.AssessRequest):
    if MOCK_MODE:
        return MOCK.ASSESS
    data = await eap_or_fallback(
        "assess", f"風險提問:{req.question}\n客戶回答:{req.answer}",
        MOCK.ASSESS, f"面談判定-{req.company_id}")
    return M.AssessResult(**data)


# ---------- 5.9 會議紀錄結構化萃取 ----------
@app.post("/api/postvisit/extract", response_model=M.ExtractResult)
async def postvisit_extract(req: M.ExtractRequest):
    if MOCK_MODE:
        return MOCK.EXTRACT
    data = await eap_or_fallback(
        "extract", f"會議紀錄全文:\n{req.notes}",
        MOCK.EXTRACT, f"會議萃取-{req.company_id}")
    return M.ExtractResult(**data)


# ---------- 5.10 拜訪後評分 ----------
@app.post("/api/postvisit/score", response_model=M.PostScoreResult)
async def postvisit_score(req: M.PostScoreRequest):
    if MOCK_MODE:
        return MOCK.POST_SCORE
    payload = json.dumps(req.extract_result.model_dump(), ensure_ascii=False)
    data = await eap_or_fallback(
        "score", f"拜訪前基準分:{req.base_score}\n萃取結果:\n{payload}",
        MOCK.POST_SCORE, f"拜訪後評分-{req.company_id}")
    data["waterfall"], data["final_score"] = fix_waterfall(data.get("waterfall", []), base_value=req.base_score)
    return M.PostScoreResult(**data)


# ---------- 5.11 情資查詢(v1.2 新增) ----------
@app.post("/api/intel/lookup")
async def intel_lookup(req: M.IntelRequest):
    key = req.query.strip()
    hit = MOCK.INTEL.get(key) or next(
        (v for v in MOCK.INTEL.values() if key and key.replace(" ", "") in v["name"].replace(" ", "")), None
    )
    # ★ 真實資料源接點:此處可改為呼叫 TWSE OpenAPI(月營收)、data.gov.tw 商工登記、
    #   司法院裁判書 API 等,將結果組成與 mock_data.INTEL 相同形狀後回傳。
    if not hit:
        err(404, "COMPANY_NOT_FOUND", "查無此公司之外部情資")
    return hit


# ---------- 5.12 報告列表(v1.2 新增) ----------
@app.post("/api/reports/list")
async def reports_list(req: M.ReportListRequest):
    items = [r for r in MOCK.REPORTS if req.status in ("全部", r["status"])]
    return {"reports": items}


# ---------- 5.13 承諾事項追蹤(v1.2 新增) ----------
@app.post("/api/commitments/list")
async def commitments_list():
    return {"commitments": MOCK.COMMITMENTS}


@app.get("/")
async def root():
    return {"service": "Credit-Lens API", "mock_mode": MOCK_MODE, "fallback_on_error": FALLBACK_ON_ERROR, "docs": "/docs"}
