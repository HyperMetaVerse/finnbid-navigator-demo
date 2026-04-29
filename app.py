import streamlit as st
from pypdf import PdfReader
import pandas as pd
from pathlib import Path

def load_demo_text(filename: str) -> str:
    p = Path(__file__).parent / filename
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""

def load_demo_df(filename: str) -> pd.DataFrame:
    p = Path(__file__).parent / filename
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)

def read_pdf(file) -> str:
    reader = PdfReader(file)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()

def read_txt(file) -> str:
    return file.read().decode("utf-8", errors="ignore").strip()

def truncate(text: str, n: int = 12000) -> str:
    if len(text) <= n:
        return text
    return text[:n] + "\n\n[TRUNCATED]"

def generic_prompts():
    base = """
You are FinnBid Navigator, an AI assistant for analysing Finnish public procurement tenders.
You must support human decision-making, not replace it.
Do NOT invent facts. If information is missing, say "Not found" and list what to verify.
When you extract any key requirement, include EVIDENCE: a short quote (max ~25 words) and where it appears (section heading / page if visible).
Output must be clear business English (British spelling).
""".strip()

    p1 = base + """

TASK 1 — Tender essentials table
Extract into a table:

- Buyer / contracting authority
- Tender title
- CPV code(s)
- Deadline (date + time)
- Submission portal
- Submission language
- Contract duration
- Award criteria (price/quality weighting if stated)
- Securities/guarantees
- Mandatory certificates/documents
- Minimum supplier requirements

OUTPUT FORMAT (CSV ONLY):
Field,Value,Evidence
""".strip()

    p2 = base + """

TASK 2 — Instant disqualifiers checklist (Go/No-Go blockers)
List ONLY hard blockers (things that would make us ineligible/non-compliant).

OUTPUT FORMAT (CSV ONLY):
Blocker,Why_it_matters,Evidence,Action,Preliminary_Go_NoGo
""".strip()

    p3 = base + """

TASK 3 — Tender Readiness Dashboard (RAG scoring)
Give Green/Yellow/Red for:
- Eligibility fit
- Financial friction
- Operational effort
- Legal/compliance risk
- Timeline risk

OUTPUT FORMAT (CSV ONLY):
Category,RAG,Reason,Evidence,Human_Check,Overall_Status,Top_Risks,Top_Internal_Questions
""".strip()

    p4 = base + """

TASK 4 — Final bid-readiness report
Split into:
A) EXEC_SUMMARY (plain text)

B) RISKS_CSV (CSV ONLY):
Risk,Impact,Mitigation,Evidence,Owner

C) NEXT_STEPS_CSV (CSV ONLY):
Step,Owner,When,Output
""".strip()

    return {
        "Prompt 1 — Essentials (template)": p1,
        "Prompt 2 — Disqualifiers (template)": p2,
        "Prompt 3 — RAG (template)": p3,
        "Prompt 4 — Final report (template)": p4,
    }
def make_prompts(tender_text: str):
    base = f"""
You are FinnBid Navigator, an AI assistant for analysing Finnish public procurement tenders.
You must support human decision-making, not replace it.
Do NOT invent facts. If information is missing, say "Not found" and list what to verify.
When you extract any key requirement, include EVIDENCE: a short quote (max ~25 words) and where it appears (section heading / page if visible).
Output must be clear business English (British spelling).

Tender document text:
\"\"\"
{truncate(tender_text)}
\"\"\"
""".strip()

    p1 = base + """

TASK 1 — Tender essentials table
Extract into a table:

- Buyer / contracting authority
- Tender title
- CPV code(s)
- Deadline (date + time)
- Submission portal
- Submission language
- Contract duration
- Award criteria (price/quality weighting if stated)
- Securities/guarantees
- Mandatory certificates/documents
- Minimum supplier requirements

Table columns:
FIELD | VALUE | EVIDENCE (quote + where)

If not found: VALUE="Not found", EVIDENCE="—".
""".strip()

    p2 = base + """

TASK 2 — Instant disqualifiers checklist (Go/No-Go blockers)
List ONLY hard blockers (things that would make us ineligible/non-compliant).

Output table:
BLOCKER | WHY IT MATTERS | EVIDENCE | ACTION (what a human should verify)

End with:
PRELIMINARY GO/NO-GO: [Go / No-Go / Needs verification] + 2–3 sentence justification.
""".strip()

    p3 = base + """

TASK 3 — Tender Readiness Dashboard (RAG scoring)
Give Green/Yellow/Red for:
- Eligibility fit
- Financial friction
- Operational effort
- Legal/compliance risk
- Timeline risk

Table columns:
CATEGORY | RAG | REASON | EVIDENCE | HUMAN CHECK

Then:
- Overall status (Green/Yellow/Red)
- Top 3 risks
- Top 3 internal questions before bidding
""".strip()

    p4 = base + """

TASK 4 — Final 1-page bid-readiness report (CEO-sendable)
Headings:
1) Executive summary (5–7 lines)
2) Tender essentials (bullets)
3) Go/No-Go recommendation (decision-support, human verifies)
4) Key risks + mitigations
5) What to verify (unknowns)
6) Next steps

Rules:
- No legal advice language.
- Use cautious wording: "potential", "appears", "requires verification".
- Include 3–6 evidence snippets inline (short quotes + where).
""".strip()

    return {
        "Prompt 1 — Essentials": p1,
        "Prompt 2 — Disqualifiers": p2,
        "Prompt 3 — RAG Dashboard": p3,
        "Prompt 4 — Final Report": p4,
    }

st.set_page_config(page_title="FinnBid Navigator (Prototype)", layout="wide")
st.title("FinnBid Navigator — Prototype")
st.caption("Decision-support for tender analysis (human-in-the-loop).")

with st.sidebar:
    st.header("Input")
    demo_mode = st.checkbox("Demo mode (load saved outputs)", value=False)
    files = st.file_uploader("Upload tender documents (optional)", type=["pdf", "txt"], accept_multiple_files=True)

tender_texts = []
if files:
    for f in files:
        if f.name.lower().endswith(".pdf"):
            tender_texts.append(read_pdf(f))
        else:
            tender_texts.append(read_txt(f))

combined_text = "\n\n--- DOCUMENT BREAK ---\n\n".join([t for t in tender_texts if t])

col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("Document preview")
    if combined_text:
        st.text_area("Extracted text (preview)", combined_text[:6000], height=260)
    else:
        st.info("Upload a PDF/TXT to begin.")

with col2:
    st.subheader("How to use (manual Claude mode)")
    st.markdown(
        """
1) Upload a tender PDF/TXT  
2) Open **Prompts** tab → copy Prompt 1 into Claude → paste result into **Essentials**  
3) Repeat for Disqualifiers, RAG, Final Report  
4) Demo the same workflow on two tenders to show repeatability
"""
    )

st.divider()
tabs = st.tabs(["Essentials", "Disqualifiers", "RAG Dashboard", "Final Report", "Prompts", "Code"])
# ---- Demo mode: preload saved outputs into session state ----
if 'demo_loaded' not in st.session_state:
    st.session_state['demo_loaded'] = False

if 'demo_mode' in locals() and demo_mode and not st.session_state['demo_loaded']:
    # Preload CSV/text into the text areas used in the app
    st.session_state["essentials_csv"] = load_demo_text("demo_essentials.csv")
    st.session_state["disqualifiers_csv"] = load_demo_text("demo_disqualifiers.csv")
    st.session_state["rag_csv"] = load_demo_text("demo_rag.csv")
    st.session_state["final_report_text"] = load_demo_text("demo_report.txt")
    st.session_state["risks_csv"] = load_demo_text("demo_risks.csv")
    st.session_state["steps_csv"] = load_demo_text("demo_next_steps.csv")
    st.session_state['demo_loaded'] = True

if 'demo_mode' in locals() and (not demo_mode):
    # If demo mode is turned off, allow reload next time it's turned on
    st.session_state['demo_loaded'] = False

def output_box(key: str):
    st.text_area("Paste Claude output here", key=key, height=280)

with tabs[0]:
    st.subheader("1) Tender essentials (CSV → table)")

    st.write("Paste CSV from Claude (columns: Field,Value,Evidence).")
    csv_text = st.text_area("Essentials CSV", key="essentials_csv", height=220)

    if st.button("Show essentials table"):
        try:
            # Read CSV from the pasted text
            from io import StringIO
            df = pd.read_csv(StringIO(csv_text))
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error("Could not read CSV. Make sure Claude output is valid CSV with header: Field,Value,Evidence.")
            st.code(str(e))

with tabs[1]:
    st.subheader("2) Instant disqualifiers (CSV → table)")

    st.write("Paste CSV from Claude (columns: Blocker,Why_it_matters,Evidence,Action,Preliminary_Go_NoGo).")
    csv_text = st.text_area("Disqualifiers CSV", key="disqualifiers_csv", height=220)

    if st.button("Show disqualifiers table"):
        try:
            from io import StringIO
            df = pd.read_csv(StringIO(csv_text))
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error("Could not read CSV. Make sure Claude output is valid CSV with the correct header row.")
            st.code(str(e))

with tabs[2]:
    st.subheader("3) Tender Readiness Dashboard (CSV → table)")

    st.write("Paste CSV from Claude (columns: Category,RAG,Reason,Evidence,Human_Check,Overall_Status,Top_Risks,Top_Internal_Questions).")
    csv_text = st.text_area("RAG CSV", key="rag_csv", height=220)

    if st.button("Show RAG table"):
        try:
            from io import StringIO
            df = pd.read_csv(StringIO(csv_text))
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error("Could not read CSV. Make sure Claude output is valid CSV with the correct header row.")
            st.code(str(e))

with tabs[3]:
    st.subheader("4) Final report (text + tables)")

    st.write("Paste the Executive Summary / narrative here (plain text):")
    st.text_area("Final report text", key="final_report_text", height=220)

    st.divider()

    st.write("Paste RISKS_CSV from Claude (columns: Risk,Impact,Mitigation,Evidence,Owner):")
    risks_csv = st.text_area("Risks CSV", key="risks_csv", height=180)

    if st.button("Show risks table"):
        try:
            from io import StringIO
            df = pd.read_csv(StringIO(risks_csv))
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error("Could not read Risks CSV. Make sure it has the correct header row.")
            st.code(str(e))

    st.divider()

    st.write("Paste NEXT_STEPS_CSV from Claude (columns: Step,Owner,When,Output):")
    steps_csv = st.text_area("Next steps CSV", key="steps_csv", height=180)

    if st.button("Show next steps table"):
        try:
            from io import StringIO
            df = pd.read_csv(StringIO(steps_csv))
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error("Could not read Next steps CSV. Make sure it has the correct header row.")
            st.code(str(e))

with tabs[4]:
    st.subheader("Prompts (copy into Claude)")

    st.info("Tip: If you want clean tables in this app, ask Claude to output CSV using the exact headers shown in each prompt.")

    if not combined_text:
        st.write("No document uploaded. Here are the prompt templates:")
        prompts = generic_prompts()
    else:
        st.write("Document uploaded. Here are prompts pre-filled with the document text:")
        prompts = make_prompts(combined_text)

    for title, prompt in prompts.items():
        with st.expander(title):
            st.code(prompt, language="markdown")

with tabs[5]:
    st.subheader("App code (read-only)")
    try:
        with open(__file__, "r", encoding="utf-8") as f:
            code_text = f.read()
        st.code(code_text, language="python")
    except Exception as e:
        st.error("Could not load app.py")
        st.code(str(e))
