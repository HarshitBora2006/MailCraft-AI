# ============================================================
#  SmartDraft AI  —  Backend  (FastAPI + OpenRouter)
#  Fixed: proper email/letter format, Hindi/English structure,
#         capitalisation, greeting, closing, subject auto-gen
#  New:   auto_subject, templates, word-count, char-count,
#         language-detect, tone-explain endpoints
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import os, requests, json, re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SmartDraft AI", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ─────────────────────────────────────────────────────────────
#  Pydantic Models
# ─────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    doc_type:           str = "email"       # "email" | "letter"
    to:                 str
    from_:              str = Field(..., alias="from")
    subject:            str
    tone:               str = "professional"
    purpose:            str
    context:            Optional[str] = ""
    language:           str = "English"     # "English" | "Hindi"
    signature_name:     Optional[str] = ""
    sender_address:     Optional[str] = ""
    recipient_address:  Optional[str] = ""

    class Config:
        populate_by_name = True

class RewriteRequest(BaseModel):
    text:     str
    mode:     str   # improve | shorten | expand | formal | casual
    language: str = "English"

class ScoreRequest(BaseModel):
    text: str

class SubjectRequest(BaseModel):
    purpose:  str
    context:  Optional[str] = ""
    tone:     str = "professional"
    language: str = "English"


# ─────────────────────────────────────────────────────────────
#  Core AI caller  (OpenRouter)
# ─────────────────────────────────────────────────────────────

def call_ai(prompt: str, temperature: float = 0.7) -> tuple[str | None, str | None]:
    if not API_KEY:
        return None, "API key not configured. Add OPENROUTER_API_KEY to .env"
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type":  "application/json",
                "HTTP-Referer":  "http://localhost:5500",
                "X-Title":       "SmartDraft AI",
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            },
            timeout=30,
        )
        data = r.json()
        if "error" in data:
            return None, data["error"].get("message", "Unknown AI error")
        choices = data.get("choices", [])
        if not choices:
            return None, "No response from AI model"
        return choices[0]["message"]["content"].strip(), None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────

def today_str(lang: str) -> str:
    now = datetime.now()
    if lang.lower() == "hindi":
        months_hi = ["जनवरी","फरवरी","मार्च","अप्रैल","मई","जून",
                     "जुलाई","अगस्त","सितम्बर","अक्टूबर","नवम्बर","दिसम्बर"]
        return f"{now.day} {months_hi[now.month-1]} {now.year}"
    return now.strftime("%d %B %Y")

def capitalise_first(s: str) -> str:
    """Ensure first letter of first word is uppercase."""
    s = s.strip()
    return s[0].upper() + s[1:] if s else s

def detect_gender_fast(name: str) -> str:
    try:
        prompt = f"""
Determine the likely gender of this name: "{name}"

Return ONLY one word:
male / female / unknown
"""
        result, _ = call_ai(prompt)

        if result:
            result = result.lower().strip()
            if result in ["male", "female"]:
                return result

        return "unknown"

    except:
        return "unknown"

def build_greeting(to: str, tone: str, lang: str) -> str:
    gender = detect_gender_fast(to)
    is_hindi = lang.lower() == "hindi"
    if is_hindi:
        if tone in ("formal","professional","strict"):
            return "महोदय," if gender == "male" else "महोदया," if gender == "female" else "महोदय/महोदया,"
        return "प्रिय मित्र," if tone == "informal" else "महोदय/महोदया,"
    # English
    if tone == "informal":
        return f"Hi {to}," if to else "Hi there,"
    if tone == "friendly":
        return f"Dear {to}," if to else "Dear Friend,"
    if gender == "male":
        return "Dear Sir,"
    if gender == "female":
        return "Dear Ma'am,"
    return "Dear Sir/Madam,"

def build_closing(tone: str, lang: str) -> str:
    is_hindi = lang.lower() == "hindi"
    if is_hindi:
        return "भवदीय," if tone in ("formal","professional","strict") else "आपका मित्र,"
    mapping = {
        "formal":       "Yours faithfully,",
        "professional": "Yours sincerely,",
        "strict":       "Yours truly,",
        "friendly":     "Warm regards,",
        "informal":     "Cheers,",
        "apologetic":   "With sincere apologies,",
        "urgent":       "Awaiting your prompt response,",
        "polite":       "With regards,",
    }
    return mapping.get(tone, "Yours sincerely,")


# ─────────────────────────────────────────────────────────────
#  PROMPT BUILDERS  (the core fix)
# ─────────────────────────────────────────────────────────────

TONE_DESCRIBE = {
    "formal":       "formal, respectful, no contractions",
    "professional": "professional, clear, polished, business-appropriate",
    "informal":     "casual, conversational, friendly, relaxed",
    "friendly":     "warm, personable, enthusiastic yet appropriate",
    "strict":       "firm, direct, authoritative, no ambiguity",
    "apologetic":   "genuinely remorseful, sincere, humble",
    "urgent":       "time-sensitive, assertive but respectful",
    "polite":       "courteous, considerate, diplomatic",
}

def build_email_prompt(req: GenerateRequest) -> str:
    lang      = req.language
    is_hindi  = lang.lower() == "hindi"
    lang_word = "Hindi (Devanagari script only)" if is_hindi else "English"
    greeting  = build_greeting(req.to, req.tone, lang)
    closing   = build_closing(req.tone, lang)
    sig       = (req.signature_name or req.from_).strip()
    tone_desc = TONE_DESCRIBE.get(req.tone, req.tone)
    ctx       = req.context.strip() if req.context else "None"

    return f"""You are an expert professional communication writer.

Write a complete, properly formatted EMAIL strictly in {lang_word}.

━━━ METADATA (do NOT print these labels in output) ━━━
To        : {req.to}
From      : {req.from_}
Subject   : {req.subject}
Purpose   : {req.purpose}
Context   : {ctx}
Tone      : {req.tone} — {tone_desc}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STRICT FORMAT (follow exactly):

{greeting}

[Opening sentence that states the purpose clearly — 1 sentence]

[Body paragraph 1 — main details, 3–4 sentences]

[Body paragraph 2 — supporting info or next steps, 2–3 sentences]

[Polite closing sentence — 1 sentence]

{closing}
{sig}

━━━ RULES ━━━
1. Write ONLY in {lang_word} — absolutely no mixing of languages
2. Every sentence must start with a CAPITAL letter
3. Do NOT use placeholders like [Your Name], [Date], [Address]
4. Do NOT include "Subject:" inside the email body
5. Use correct punctuation and grammar throughout
6. Word count: 120–200 words
7. Tone must match: {tone_desc}
8. Output ONLY the email text — no commentary, no headers, no markdown
"""


def build_letter_prompt(req: GenerateRequest) -> str:
    lang      = req.language
    is_hindi  = lang.lower() == "hindi"
    lang_word = "Hindi (Devanagari script only)" if is_hindi else "English"
    date      = today_str(lang)
    greeting  = build_greeting(req.to, req.tone, lang)
    closing   = build_closing(req.tone, lang)
    sig       = (req.signature_name or req.from_).strip()
    tone_desc = TONE_DESCRIBE.get(req.tone, req.tone)
    ctx       = req.context.strip() if req.context else "None"

    sender_addr    = req.sender_address.strip()    if req.sender_address    else ""
    recipient_addr = req.recipient_address.strip() if req.recipient_address else ""

    # Build address blocks cleanly
    sender_block    = f"{req.from_}\n{sender_addr}"    if sender_addr    else req.from_
    recipient_block = f"{req.to}\n{recipient_addr}"    if recipient_addr else req.to

    return f"""You are an expert formal letter writer.

Write a complete, properly formatted FORMAL LETTER strictly in {lang_word}.

━━━ DETAILS (do NOT print these labels) ━━━
Sender    : {req.from_}
Recipient : {req.to}
Subject   : {req.subject}
Purpose   : {req.purpose}
Context   : {ctx}
Tone      : {req.tone} — {tone_desc}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STRICT FORMAT (copy this structure exactly):

{sender_block}

{date}

To,
{recipient_block}

Subject: {req.subject}

{greeting}

[Opening paragraph — state purpose clearly, 2–3 sentences]

[Body paragraph — main content, details, request or information, 3–4 sentences]

[Closing paragraph — polite next step or request for action, 1–2 sentences]

{closing}
{sig}

━━━ RULES ━━━
1. Write ONLY in {lang_word} — no language mixing
2. Every sentence must begin with a CAPITAL letter
3. Do NOT use placeholder text like [Your Address], [Name], [Date]
4. Use the exact date: {date}
5. Follow Indian formal letter conventions
6. Correct grammar and punctuation throughout
7. Word count: 150–220 words
8. Output ONLY the letter text — no commentary, no markdown
"""


def build_subject_prompt(req: SubjectRequest) -> str:
    lang      = req.language
    is_hindi  = lang.lower() == "hindi"
    lang_word = "Hindi" if is_hindi else "English"
    ctx       = req.context.strip() if req.context else "None"
    return f"""Generate 5 professional email/letter subject lines in {lang_word}.

Purpose : {req.purpose}
Context : {ctx}
Tone    : {req.tone}

Rules:
- Return ONLY a JSON array of 5 strings, no other text
- Each subject must be concise (5–10 words)
- Each must start with a capital letter
- No markdown, no numbering, just the JSON array
- Language: {lang_word} only

Example output: ["Subject one", "Subject two", "Subject three", "Subject four", "Subject five"]
"""


def build_rewrite_prompt(req: RewriteRequest) -> str:
    lang_word = "Hindi (Devanagari)" if req.language.lower() == "hindi" else "English"
    instructions = {
        "improve":  "Improve clarity, flow, grammar, and overall professionalism.",
        "shorten":  "Shorten significantly — keep every key point but remove all redundancy.",
        "expand":   "Expand with more detail, context, examples, and supporting sentences.",
        "formal":   "Rewrite in a highly formal, professional tone suitable for executive correspondence.",
        "casual":   "Rewrite in a natural, relaxed, conversational tone.",
    }
    return f"""Rewrite the following text in {lang_word}.

Instruction: {instructions.get(req.mode, 'Improve the text.')}

ORIGINAL TEXT:
{req.text}

VERY IMPORTANT RULES:
- The input is a FULL LETTER (not just paragraph)
- You MUST preserve COMPLETE format and structure
- DO NOT remove or change:
  - From section
  - Date
  - To section
  - Subject line
  - Greeting
  - Closing & Signature
- Only rewrite the BODY content (main paragraphs)
- Preserve the original meaning and purpose
- Every sentence must start with a capital letter
- Do NOT use placeholders
- Output ONLY the rewritten text, no commentary
- Language: {lang_word} only
LETTER:
{req.text}

----------------------------------------

Rewrite the letter with SAME format.

⚠️ OUTPUT RULES:
- Keep exact structure and spacing
- Only improve the paragraph content
- Do NOT remove headings
- Do NOT add extra text
- Output FULL LETTER only
"""


def build_score_prompt(text: str) -> str:
    return f"""Analyse this email or letter and return a quality score.

TEXT:
{text}

Return ONLY valid JSON (no markdown, no extra text):
{{
  "clarity": <integer 1-10>,
  "tone": <integer 1-10>,
  "grammar": <integer 1-10>,
  "professionalism": <integer 1-10>,
  "structure": <integer 1-10>,
  "overall": <integer 1-10>,
  "strengths": "<one sentence about what is done well>",
  "improvements": "<one sentence — single most impactful improvement>",
  "grade": "<A / B / C / D>"
}}
"""


# ─────────────────────────────────────────────────────────────
#  Post-processing  — fix common AI capitalisation issues
# ─────────────────────────────────────────────────────────────

def fix_capitalisation(text: str, lang: str) -> str:
    """Ensure every sentence starts with a capital letter (English only)."""
    if lang.lower() == "hindi":
        return text
    # Split on sentence-ending punctuation and capitalise next word
    def cap_after(m):
        return m.group(0)[:-1] + " " + m.group(0)[-1].upper() if m.group(0)[-1].islower() else m.group(0)
    # Fix line-start lowercase
    lines = text.split("\n")
    fixed = []
    for line in lines:
        stripped = line.lstrip()
        if stripped and stripped[0].islower():
            line = line[: len(line) - len(stripped)] + stripped[0].upper() + stripped[1:]
        fixed.append(line)
    return "\n".join(fixed)


# ─────────────────────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "SmartDraft AI v2.0 running", "docs": "/docs"}


@app.post("/generate")
def generate(req: GenerateRequest):
    if not API_KEY:
        raise HTTPException(400, "OPENROUTER_API_KEY not set in .env")

    if req.doc_type == "letter":
        prompt = build_letter_prompt(req)
    else:
        prompt = build_email_prompt(req)

    output, err = call_ai(prompt, temperature=0.65)
    if err:
        raise HTTPException(500, err)

    output = fix_capitalisation(output, req.language)

    word_count = len(output.split())
    char_count = len(output)

    return {
        "success":    True,
        "doc_type":   req.doc_type,
        "content":    output,
        "word_count": word_count,
        "char_count": char_count,
        "language":   req.language,
    }


@app.post("/auto-subject")
def auto_subject(req: SubjectRequest):
    if not API_KEY:
        raise HTTPException(400, "OPENROUTER_API_KEY not set in .env")

    prompt = build_subject_prompt(req)
    output, err = call_ai(prompt, temperature=0.8)
    if err:
        raise HTTPException(500, err)

    # Parse JSON array safely
    try:
        clean = re.sub(r"```json|```", "", output).strip()
        subjects = json.loads(clean)
        if isinstance(subjects, list):
            subjects = [capitalise_first(s) for s in subjects]
        else:
            subjects = [capitalise_first(output)]
    except Exception:
        # Fallback: split lines
        subjects = [capitalise_first(l.strip(" -•1234567890.")) 
                    for l in output.split("\n") if l.strip()][:5]

    return {"success": True, "subjects": subjects}


@app.post("/rewrite")
def rewrite(req: RewriteRequest):
    if not API_KEY:
        raise HTTPException(400, "OPENROUTER_API_KEY not set in .env")

    prompt = build_rewrite_prompt(req)
    output, err = call_ai(prompt, temperature=0.7)
    if err:
        raise HTTPException(500, err)

    output = fix_capitalisation(output, req.language)
    return {"success": True, "content": output, "mode": req.mode}


@app.post("/score")
def score_doc(req: ScoreRequest):
    if not API_KEY:
        raise HTTPException(400, "OPENROUTER_API_KEY not set in .env")

    prompt = build_score_prompt(req.text)
    output, err = call_ai(prompt, temperature=0.3)
    if err:
        raise HTTPException(500, err)

    try:
        clean  = re.sub(r"```json|```", "", output).strip()
        parsed = json.loads(clean)
    except Exception:
        raise HTTPException(500, "AI returned invalid score format")

    return {"success": True, "score": parsed}


@app.get("/health")
def health():
    return {
        "status":   "ok",
        "api_key":  "set" if API_KEY else "missing",
        "version":  "2.0",
    }