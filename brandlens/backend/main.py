import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="BrandLens API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

SLANG = {"gonna": "going to", "awesome": "excellent",
         "super": "very", "kinda": "somewhat"}

RULES = [
    {"id": "TERM-01", "type": "Terminology", "severity": "low",
     "pattern": r"\bclients?\b",
     "rule": "Always say 'customer(s)', never 'client(s)'.",
     "fix": lambda m: "customers" if m.lower().endswith("s") else "customer"},
    {"id": "TERM-02", "type": "Terminology", "severity": "low",
     "pattern": r"\bcheap\b",
     "rule": "Use 'affordable' instead of 'cheap'.",
     "fix": lambda m: "affordable"},
    {"id": "TONE-01", "type": "Tone", "severity": "low",
     "pattern": r"\b(gonna|awesome|super|kinda)\b",
     "rule": "Tone is warm and professional; avoid slang.",
     "fix": lambda m: SLANG[m.lower()]},
    {"id": "TONE-02", "type": "Tone", "severity": "low",
     "pattern": r"!+",
     "rule": "Avoid exclamation marks in product copy.",
     "fix": lambda m: "."},
    {"id": "CLAIM-01", "type": "Unsupported claim", "severity": "high",
     "pattern": r"#1|number one|100% guaranteed|best in [a-z]+",
     "rule": "Superlatives and guarantees need approved evidence. None on file.",
     "fix": lambda m: "backed by our 30-day return policy"
                      if "guarantee" in m.lower() else "a trusted choice"},
    {"id": "FACT-01", "type": "Outdated fact", "severity": "high",
     "pattern": r"₹\s?499",
     "rule": "Approved fact: Starter Pack price is ₹599.",
     "fix": lambda m: "₹599"},
    {"id": "FACT-02", "type": "Outdated fact", "severity": "high",
     "pattern": r"free shipping on all orders",
     "rule": "Approved fact: free shipping applies to orders above ₹999.",
     "fix": lambda m: "free shipping on orders above ₹999"},
]


class Draft(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/rules")
def rules():
    return [{k: r[k] for k in ("id", "type", "severity", "rule")} for r in RULES]


@app.post("/review")
def review(draft: Draft):
    findings = []
    for r in RULES:
        for m in re.finditer(r["pattern"], draft.text, re.IGNORECASE):
            findings.append({
                "rule_id": r["id"],
                "type": r["type"],
                "severity": r["severity"],
                "quoted_text": m.group(0),
                "start": m.start(),
                "end": m.end(),
                "why": r["rule"],
                "suggestion": r["fix"](m.group(0)),
            })
    findings.sort(key=lambda f: f["start"])
    return {"count": len(findings), "findings": findings}