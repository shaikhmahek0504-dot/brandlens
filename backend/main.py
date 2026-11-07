import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BrandLens</title>
<style>
:root{--bg:#f6f8fc;--card:#fff;--tx:#1b2438;--mu:#5b6579;--bd:#d9dfec;--ac:#2f6fed;--ok:#1f8f4e;--wa:#b36b00;--er:#d23b3b;--hl:#fff1c2}
@media (prefers-color-scheme:dark){:root{--bg:#12151d;--card:#1b2030;--tx:#e8ecf6;--mu:#9aa5bd;--bd:#2d3550;--ac:#6b9bff;--ok:#4cc27f;--wa:#f0b04a;--er:#ff7a7a;--hl:#4a3f12}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:16px}h1{font-size:22px;margin:0}h2{font-size:16px;margin:0 0 8px}
.sub,.src,.note,.log{color:var(--mu);font-size:13px}.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:14px;margin-bottom:12px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;justify-content:space-between}
button{font:inherit;border:1px solid var(--bd);background:var(--card);color:var(--tx);border-radius:8px;padding:7px 12px;cursor:pointer}
button.p{background:var(--ac);border-color:var(--ac);color:#fff}button.ok{background:var(--ok);border-color:var(--ok);color:#fff}
button:disabled{opacity:.45}.seg button.on{background:var(--ac);color:#fff;border-color:var(--ac)}
textarea,input{width:100%;font:inherit;color:var(--tx);background:var(--bg);border:1px solid var(--bd);border-radius:8px;padding:8px}textarea{min-height:110px}
.f{border:1px solid var(--bd);border-left:4px solid var(--wa);border-radius:8px;padding:10px;margin-top:8px}.f.high{border-left-color:var(--er)}
.tag{font-size:11px;font-weight:700;text-transform:uppercase;color:var(--mu)}mark{background:var(--hl);color:inherit;padding:0 3px;border-radius:3px}
.pill{padding:2px 10px;border-radius:99px;font-size:12px;font-weight:700;border:1px solid var(--bd)}
</style></head><body><main>
<div class="row"><div><h1>BrandLens</h1><div class="sub">AI-assisted brand review before publication · live API</div></div>
<div class="seg" id="seg"><button data-r="Creator" class="on">Creator</button> <button data-r="Manager">Manager</button></div></div>
<div class="card" style="margin-top:12px"><h2>1. Draft content</h2><textarea id="draft"></textarea>
<div class="row" style="margin-top:8px"><span class="src" id="msg"></span><button class="p" id="rev">Review against brand rules</button></div></div>
<div class="card"><h2>2. Findings</h2><div id="finds" class="src">Press “Review” to check the draft.</div></div>
<div class="card"><h2>3. Approval workflow</h2>
<div class="row"><div>Version <b id="ver">0</b> · Status: <span class="pill" id="stat">Draft</span></div><button class="p" id="sub">Submit for approval</button></div>
<div id="mgr" hidden style="margin-top:10px"><input id="cm" placeholder="Reviewer comment (optional)">
<div class="row" style="margin-top:8px;justify-content:flex-start"><button class="ok" id="ap">Approve</button><button id="ch">Request changes</button></div></div>
<div class="log" id="log" style="margin-top:10px"></div></div>
<p class="note">Findings come from the BrandLens API (/review) and cite the approved rule behind each flag. Suggestions are never applied without a human clicking Accept. AI use: rule engine in the backend; no content is sent to third parties in this version.</p>
</main><script>
var $=function(i){return document.getElementById(i)};
function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
$("draft").value="Our awesome new Starter Pack is the #1 skincare choice for clients in India! Get it now for just ₹499 with free shipping on all orders. It’s super gentle and 100% guaranteed to work!";
var dismissed={},reviewed=false,role="Creator",ver=0,status="Draft",hist=[],found=[];
function now(){return new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}
function log(t){hist.unshift(now()+" · "+t);$("log").innerHTML=hist.slice(0,8).map(esc).join("<br>")}
function review(){
 $("msg").textContent="Reviewing…";
 return fetch("/review",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:$("draft").value})})
 .then(function(r){if(!r.ok)throw new Error(r.status);return r.json()})
 .then(function(d){reviewed=true;found=d.findings.filter(function(f){return !dismissed[f.rule_id+"|"+f.quoted_text.toLowerCase()]});$("msg").textContent="";render()})
 .catch(function(){$("msg").textContent="Could not reach the review API. Try again.";});
}
function render(){
 if(!found.length){$("finds").innerHTML="<b style='color:var(--ok)'>No open issues. Ready to submit.</b>";return}
 $("finds").innerHTML="<div class='src'>"+found.length+" open issue(s). Nothing changes unless you accept it.</div>"+found.map(function(f,n){
 return "<div class='f "+f.severity+"'><div class='tag'>"+esc(f.type)+" · "+f.severity+" · "+esc(f.rule_id)+"</div>"+
 "<div>Flagged: <mark>"+esc(f.quoted_text)+"</mark></div><div class='src'>Why: "+esc(f.why)+"</div>"+
 "<div>Suggested: <b style='color:var(--ok)'>"+esc(f.suggestion)+"</b></div>"+
 "<div class='row' style='justify-content:flex-start;margin-top:6px'><button class='p' data-a='"+n+"'>Accept</button><button data-x='"+n+"'>Reject</button></div></div>"}).join("");
}
function setStatus(s){status=s;var e=$("stat");e.textContent=s;$("mgr").hidden=!(role==="Manager"&&s==="Pending review");$("sub").disabled=role!=="Creator"||s==="Pending review"||s==="Approved"}
$("rev").onclick=function(){review().then(function(){log("Creator ran AI review")})};
$("finds").onclick=function(e){var a=e.target.getAttribute("data-a"),x=e.target.getAttribute("data-x"),f,t;
 if(a!==null){f=found[+a];t=$("draft").value;$("draft").value=t.slice(0,f.start)+f.suggestion+t.slice(f.end);log("Accepted “"+f.quoted_text+"” → “"+f.suggestion+"”");review()}
 else if(x!==null){f=found[+x];dismissed[f.rule_id+"|"+f.quoted_text.toLowerCase()]=1;log("Rejected suggestion for “"+f.quoted_text+"”");review()}};
$("sub").onclick=function(){if(!reviewed){alert("Run the review first.");return}ver++;$("ver").textContent=ver;setStatus("Pending review");log("Creator submitted version "+ver+" ("+found.length+" open issue(s))")};
$("ap").onclick=function(){setStatus("Approved");log("Manager approved. "+($("cm").value||"No comment"))};
$("ch").onclick=function(){setStatus("Changes requested");log("Manager requested changes. "+($("cm").value||"No comment"))};
$("seg").onclick=function(e){var r=e.target.getAttribute("data-r");if(!r)return;role=r;[].forEach.call($("seg").children,function(b){b.className=b.getAttribute("data-r")===r?"on":""});setStatus(status)};
setStatus("Draft");
</script></body></html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE
