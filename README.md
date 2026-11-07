# BrandLens
AI-assisted brand review before publication.

Live demo: https://brandlens-36sk.onrender.com
(Free hosting: the first load may take about a minute.)

## What it does
Checks draft content against brand rules and approved facts, flags tone,
terminology, outdated facts and unsupported claims, cites the rule behind
each flag, and suggests a fix. Creators accept or reject every suggestion;
managers approve or request changes.

## How to try it
1. Open the live link and press "Review against brand rules".
2. Accept or reject findings; the draft updates only when you accept.
3. Submit for approval, switch to "Manager", and approve.

## Architecture
Browser page (HTML/JS) -> FastAPI /review endpoint -> rule engine ->
findings (rule ID, quoted text, reason, suggested fix) -> human decision ->
approval workflow.

## Tech
Python, FastAPI, Pydantic, Uvicorn, plain HTML/CSS/JS, hosted on Render.

## Status
Working: review API, cited findings, accept/reject, creator and manager
views, approval workflow with activity log.
Planned: retrieval + LLM review over uploaded guidelines, image and
accessibility checks, database storage and login, guideline upload,
governance dashboard.
Limitations: approval workflow state lives in the browser session only;
rules are a fixed demo brand (Acme Naturals).

## AI and tools disclosure
AI assistance (Claude) was used for planning and drafting code. The
current review engine is rule-based; no user content is sent to external
AI services in this version.

## Run locally
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

## Author
Mahek Shaikh, individual participant
