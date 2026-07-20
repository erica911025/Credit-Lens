# mock_data.py — MOCK_MODE 用的規格書第 5 章範例 JSON(Demo 保險絲,7.3)
# 與前端 src/mock.js 逐欄位一致;任何變更需先改規格書再同步兩邊。

FINANCE = {
    "agent": "finance", "score": 58,
    "findings": [
        {"text": "近三年資本支出年增 82%,自由現金流連續兩年為負,擴產資金高度依賴外部融資。", "cite": "113 年度財報 p.45", "confidence": 0.92},
        {"text": "流動比率 0.94,低於同業中位數 1.6,短期償債能力偏弱。", "cite": "TWSE 財報摘要 API", "confidence": 0.88},
    ],
}

TECH = {
    "agent": "tech", "score": 81,
    "findings": [
        {"text": "固態電解質相關專利 47 件,12 件被國際大廠引用,技術護城河明確。", "cite": "TIPO 專利檢索", "confidence": 0.95},
        {"text": "研報預估固態電池 2028 市場 CAGR 34%,惟量產良率仍在爬坡。", "cite": "產業研究報告 2025Q4", "confidence": 0.74},
    ],
}

JUDGE = {
    "agent": "judge",
    "contradictions": [
        {"title": "量產時程 vs 資金缺口", "detail": "技術面預估 2027 量產放量,但財務面現金流為負、流動比率僅 0.94,資金銜接方案未被說明,列為面談必問。", "severity": "high"},
        {"title": "客戶集中風險未被技術面納入", "detail": "前兩大客戶佔營收 61%,若即為專利引用大廠,技術授權與訂單高度綁定,風險應合併評估。", "severity": "medium"},
    ],
    "verdict": "技術護城河成立(採信);財務體質偏弱(採信);市場預估缺客戶結構佐證(部分採信)。綜合 71 分,建議附條件核貸並於面談釐清資金方案。",
    "final_score": 71,
    "waterfall": [
        {"label": "基礎分", "value": 60, "type": "base"},
        {"label": "技術護城河", "value": 18, "type": "plus"},
        {"label": "產業景氣", "value": 9, "type": "plus"},
        {"label": "財務體質", "value": -12, "type": "minus"},
        {"label": "客戶集中", "value": -4, "type": "minus"},
    ],
}

BRIEF = {
    "radar": [
        {"key": "tech", "label": "技術壁壘", "score": 82, "benchmark": 55, "agent": "tech", "reason": "專利 47 件、12 件遭國際大廠引用,近三年申請量成長 3 倍。", "cites": ["TIPO 專利檢索"]},
        {"key": "market", "label": "市場規模", "score": 74, "benchmark": 60, "agent": "tech", "reason": "2028 CAGR 預估 34%,惟量產良率爬坡中,放量時點不確定。", "cites": ["產業研報 2025Q4"]},
        {"key": "finance", "label": "財務體質", "score": 48, "benchmark": 65, "agent": "finance", "reason": "自由現金流連兩年為負、流動比率 0.94,為六維最弱項。", "cites": ["113 年報 p.45"]},
        {"key": "legal", "label": "訴訟風險", "score": 71, "benchmark": 70, "agent": "judge", "reason": "近五年僅一件勞資調解已和解,無專利侵權訴訟在案。", "cites": ["司法院裁判書 API"]},
        {"key": "esg", "label": "ESG 合規", "score": 66, "benchmark": 68, "agent": "judge", "reason": "一筆廢水裁罰(12 萬)已改善結案,勞動部名單無紀錄。", "cites": ["環境部裁罰紀錄"]},
        {"key": "macro", "label": "產業景氣", "score": 77, "benchmark": 62, "agent": "finance", "reason": "EV 滲透率上升、鋰價回落 40%,循環位置有利。", "cites": ["FRED 指數"]},
    ],
    "questions": [
        {"id": 1, "dim": "財務體質", "q": "自由現金流連續兩年為負,量產前 2–3 年資金缺口的具體銜接方案?", "why": "財務分析 Agent 判定最大違約風險(113 年報 p.45)"},
        {"id": 2, "dim": "市場規模", "q": "目前量產良率實際數字?損益兩平所需良率門檻?", "why": "技術情報 Agent 發現新聞提及良率仍在爬坡(GDELT)"},
        {"id": 3, "dim": "技術壁壘", "q": "前兩大客戶是否即為專利主要引用方?合約年限?", "why": "審查官交叉質詢發現客戶集中與技術授權可能綁定"},
    ],
}

ASSESS = {
    "verdict": "partial",
    "reason": "提出資金方向但屬意向性質、未具約束力,時程未完全對上。",
    "follow": "追問:意向書是否具法律約束力?交割時點?募資延遲的備援方案?",
}

EXTRACT = {
    "commitments": [
        {"item": "提供 B 輪投資意向書副本", "owner": "財務長 林OO", "due": "115-08-15"},
        {"item": "提供良率改善合約", "owner": "技術長 張OO", "due": "115-08-15"},
    ],
    "responses": [
        {"risk": "資金銜接方案", "summary": "B 輪意向書 8 億、Q4 交割,惟未具約束力", "verdict": "partial"},
        {"risk": "量產良率門檻", "summary": "現況 63%/門檻 75%,有改善合約與明確時程", "verdict": "resolved"},
        {"risk": "客戶集中與專利綁定", "summary": "證實綁定、2027 到期,續約中且第三客戶送樣", "verdict": "partial"},
    ],
    "new_risks": [{"text": "廠房二期再投入 12 億,原財報未揭露,資金缺口實際擴大。"}],
}

POST_SCORE = {
    "final_score": 68,
    "waterfall": [
        {"label": "拜訪前基準", "value": 71, "type": "base"},
        {"label": "良率已化解", "value": 8, "type": "plus"},
        {"label": "承諾可驗證", "value": 4, "type": "plus"},
        {"label": "資金未落定", "value": -6, "type": "minus"},
        {"label": "未揭露支出", "value": -9, "type": "minus"},
    ],
    "recommendation": "附條件核貸:以 8/15 承諾文件到齊 + B 輪正式簽約為撥款前提;二期廠房資金計畫須補件。",
}

INTEL = {
    "12345678": {
        "id": "12345678", "name": "XX 固態電池科技股份有限公司", "industry": "儲能/電池",
        "reg": {"capital": "12.5 億", "founded": "108-03-15", "chairman": "王OO",
                "directors": ["王OO(董事長)", "林OO(董事/財務長)", "張OO(董事/技術長)", "陳OO(獨立董事)"],
                "status": "核准設立", "address": "新竹科學園區XX路 66 號"},
        "revenue": [
            {"m": "115-01", "val": 2.1, "yoy": 18}, {"m": "115-02", "val": 1.8, "yoy": 12},
            {"m": "115-03", "val": 2.6, "yoy": 31}, {"m": "115-04", "val": 2.4, "yoy": 22},
            {"m": "115-05", "val": 2.9, "yoy": 38}, {"m": "115-06", "val": 3.2, "yoy": 45},
        ],
        "lawsuits": [{"no": "113年度勞訴字第88號", "cause": "給付資遣費(勞資調解)", "result": "和解成立", "date": "113-11-02"}],
        "fines": [{"agency": "環境部", "law": "水污染防治法", "amount": "12 萬", "status": "已改善結案", "date": "113-05-20"}],
        "patents": {"count": 47, "cited": 12, "trend": [6, 9, 14, 18]},
        "news": [
            {"date": "115-07-10", "title": "固態電池量產良率挑戰仍在,業者:明年 Q2 達損益兩平門檻", "senti": "neu"},
            {"date": "115-06-28", "title": "XX 電池獲兩家創投 B 輪意向,擬募 8 億擴產", "senti": "pos"},
            {"date": "115-06-14", "title": "國際大廠加碼固態電池訂單,台鏈受惠", "senti": "pos"},
            {"date": "115-05-30", "title": "鋰價回落 4 成,電池廠成本壓力緩解", "senti": "pos"},
        ],
        "graph": {
            "nodes": [
                {"id": "12345678", "label": "XX固態電池", "type": "self", "x": 320, "y": 170},
                {"id": "45678901", "label": "AA電解質材料", "type": "supplier", "x": 120, "y": 80, "warn": True},
                {"id": "56789012", "label": "BB精密設備", "type": "supplier", "x": 120, "y": 260},
                {"id": "67890123", "label": "CC汽車集團", "type": "customer", "x": 520, "y": 80},
                {"id": "78901234", "label": "DD儲能系統", "type": "customer", "x": 520, "y": 260},
                {"id": "89012345", "label": "EE創投控股", "type": "related", "x": 320, "y": 320},
            ],
            "edges": [
                {"from": "45678901", "to": "12345678", "rel": "supply"},
                {"from": "56789012", "to": "12345678", "rel": "supply"},
                {"from": "12345678", "to": "67890123", "rel": "supply"},
                {"from": "12345678", "to": "78901234", "rel": "supply"},
                {"from": "89012345", "to": "12345678", "rel": "board"},
                {"from": "67890123", "to": "12345678", "rel": "patent"},
            ],
            "alert": "上游供應商「AA電解質材料」近兩季營收衰退 34%、傳出財務吃緊——若其斷料,將直接衝擊量產時程(隱藏風險由圖譜推理發現)。",
        },
    },
}

REPORTS = [
    {"date": "115-07-16", "company": "XX 固態電池科技股份有限公司", "id": "12345678", "version": "拜訪後終版", "score": 68, "status": "已送審"},
    {"date": "115-07-12", "company": "XX 固態電池科技股份有限公司", "id": "12345678", "version": "拜訪前基準", "score": 71, "status": "已核定"},
    {"date": "115-07-11", "company": "ΔΔ 基因定序服務股份有限公司", "id": "34567890", "version": "拜訪前基準", "score": 74, "status": "已核定"},
    {"date": "115-07-08", "company": "OO 低軌衛星通訊股份有限公司", "id": "23456789", "version": "拜訪前基準", "score": 62, "status": "草稿"},
]

COMMITMENTS = [
    {"company": "XX 固態電池", "item": "提供 B 輪投資意向書副本", "owner": "財務長 林OO", "due": "115-08-15"},
    {"company": "XX 固態電池", "item": "提供良率改善合約", "owner": "技術長 張OO", "due": "115-08-15"},
    {"company": "ΔΔ 基因定序", "item": "補送 FDA 送件收執證明", "owner": "法務長 吳OO", "due": "115-07-18"},
    {"company": "ΔΔ 基因定序", "item": "提供前三大客戶合約摘要", "owner": "業務副總 許OO", "due": "115-07-25"},
]
