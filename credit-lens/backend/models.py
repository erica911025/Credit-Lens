# models.py — 規格書第 6 章共用資料結構(Pydantic 自動驗證)
# 列舉值一律逐一列出(7.1 命名一致性),回應欄位 snake_case
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# ---------- Requests ----------
class ReviewRequest(BaseModel):
    company_id: str = Field(min_length=8, max_length=8)  # 統一編號 8 碼字串
    company_name: str = ""


class JudgeRequest(BaseModel):
    company_id: str
    finance_result: "AgentResult"
    tech_result: "AgentResult"


class ReportRequest(BaseModel):
    company_id: str
    judge_result: "JudgeResult"


class AssessRequest(BaseModel):
    company_id: str
    question_id: int
    question: str
    answer: str


class ExtractRequest(BaseModel):
    company_id: str
    notes: str


class PostScoreRequest(BaseModel):
    company_id: str
    base_score: int = Field(ge=0, le=100)
    extract_result: "ExtractResult"


class IntelRequest(BaseModel):
    query: str


class ReportListRequest(BaseModel):
    status: str = "全部"


# ---------- 6.1 / 6.2 ----------
class Finding(BaseModel):
    text: str
    cite: str  # 必填:無來源的發現後端直接丟棄(防幻覺)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)


class AgentResult(BaseModel):
    agent: Literal["finance", "tech"]
    score: int = Field(ge=0, le=100)
    findings: List[Finding]


# ---------- 6.3 / 6.4 / 6.5 ----------
class Contradiction(BaseModel):
    title: str
    detail: str
    severity: Literal["high", "medium", "low"]


class WaterfallItem(BaseModel):
    label: str
    value: int
    type: Literal["base", "plus", "minus"]


class JudgeResult(BaseModel):
    agent: Literal["judge"] = "judge"
    contradictions: List[Contradiction]
    verdict: str
    final_score: int = Field(ge=0, le=100)
    waterfall: List[WaterfallItem]


# ---------- 6.6 / 6.7(5.7 拜訪前情資)----------
class RadarDim(BaseModel):
    key: Literal["tech", "market", "finance", "legal", "esg", "macro"]
    label: str
    score: int = Field(ge=0, le=100)
    benchmark: int = Field(ge=0, le=100)
    agent: Literal["finance", "tech", "judge"]
    reason: str
    cites: List[str]


class Question(BaseModel):
    id: int
    dim: str
    q: str
    why: str


class BriefResult(BaseModel):
    radar: List[RadarDim]
    questions: List[Question]


# ---------- 6.8 / 6.9 / 6.10 ----------
class AssessResult(BaseModel):
    verdict: Literal["resolved", "partial", "unresolved"]
    reason: str
    follow: str


class Commitment(BaseModel):
    item: str
    owner: str
    due: str


class RiskResponse(BaseModel):
    risk: str
    summary: str
    verdict: Literal["resolved", "partial", "unresolved"]


class NewRisk(BaseModel):
    text: str


class ExtractResult(BaseModel):
    commitments: List[Commitment]
    responses: List[RiskResponse]
    new_risks: List[NewRisk]


class PostScoreResult(BaseModel):
    final_score: int = Field(ge=0, le=100)
    waterfall: List[WaterfallItem]
    recommendation: str


class ReportResult(BaseModel):
    report_url: str


JudgeRequest.model_rebuild()
ReportRequest.model_rebuild()
PostScoreRequest.model_rebuild()
