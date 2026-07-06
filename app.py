import streamlit as st
import pandas as pd
import pypdf
import json
import random
from datetime import datetime
from google import genai
from google.genai import types

# Page Config
st.set_page_config(page_title="CISSP Pocket Coach", page_icon="🛡️", layout="centered")

# --- INITIALIZE STATE & API ---
if "api_key" not in st.session_state:
    st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", "")

if "pdf_texts" not in st.session_state:
    st.session_state.pdf_texts = {} # {filename: [page_1_text, page_2_text, ...]}
if "covered_pages" not in st.session_state:
    st.session_state.covered_pages = {} # {filename: set(page_indices)}
if "mistake_log" not in st.session_state:
    st.session_state.mistake_log = []
if "current_q" not in st.session_state:
    st.session_state.current_q = None

st.title("🛡️ CISSP AI Pocket Coach")

# Check for API Key
api_key = st.session_state.api_key or st.sidebar.text_input("Enter Gemini API Key:", type="password")
if not api_key:
    st.warning("⚠️ Please enter your Gemini API Key in the sidebar or app secrets to start.")
    st.stop()

client = genai.Client(api_key=api_key)

# --- SIDEBAR: PDF UPLOADER ---
with st.sidebar:
    st.header("📚 Study Shelf")
    uploaded_files = st.file_uploader("Upload CISSP PDFs (e.g., Memory Palace):", type=["pdf"], accept_multiple_files=True)
    if uploaded_files:
        for pdf_file in uploaded_files:
            if pdf_file.name not in st.session_state.pdf_texts:
                reader = pypdf.PdfReader(pdf_file)
                pages = [page.extract_text() for page in reader.pages]
                st.session_state.pdf_texts[pdf_file.name] = pages
                st.session_state.covered_pages[pdf_file.name] = set()
        st.success(f"Loaded {len(st.session_state.pdf_texts)} source(s)!")

# Tabs
tab_quiz, tab_progress, tab_mistakes, tab_ext = st.tabs([
    "🎯 Live Quiz", "📊 % Coverage", "🧠 Mistake Log", "➕ Add External Q"
])

# --- TAB 1: LIVE AI QUIZ ---
with tab_quiz:
    if not st.session_state.pdf_texts:
        st.info("👈 Upload your study PDF (like *The Memory Palace*) in the sidebar arrow menu first!")
    else:
        src_choice = st.selectbox("Select Source Book:", list(st.session_state.pdf_texts.keys()))
        domain_choice = st.selectbox("Focus Area:", ["Mixed / Random Page"] + [f"Domain {i}" for i in range(1, 9)])
        
        if st.button("⚡ Generate Fresh AI Question", use_container_width=True):
            pages = st.session_state.pdf_texts[src_choice]
            # Pick a random page from the document to quiz on
            page_idx = random.randint(0, len(pages) - 1)
            page_text = pages[page_idx]
            
            prompt = f"""
            You are a strict CISSP exam coach. Based ONLY on the provided textbook page excerpt below, generate ONE challenging multiple-choice question relevant to {domain_choice}.
            
            Text Excerpt (Page {page_idx + 1}):
            {page_text[:2000]}
            
            Return strictly valid JSON with these keys:
            "question": "string",
            "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
            "correct": "A) option1" (must match one option exactly),
            "explanation": "Why correct & why others are wrong",
            "citation": "Exact section/topic name mentioned in text"
            """
            
            with st.spinner(f"Reading Page {page_idx + 1} and writing question..."):
                try:
                    res = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(response_mime_type="application/json")
                    )
                    q_data = json.loads(res.text)
                    q_data["page"] = page_idx + 1
                    q_data["source"] = src_choice
                    st.session_state.current_q = q_data
                except Exception as e:
                    st.error(f"Error generating question: {e}")

        # Display Current Question
        if st.session_state.current_q:
            q = st.session_state.current_q
            st.markdown("---")
            st.caption(f"📖 **Source:** {q['source']} | **Page:** {q['page']} | **Topic:** {q['citation']}")
            st.write(f"**{q['question']}**")
            
            user_ans = st.radio("Select your choice:", q["options"], index=None, key=f"radio_{q['question'][:15]}")
            
            if st.button("Submit Answer", type="primary"):
                if user_ans:
                    # Mark page as covered!
                    st.session_state.covered_pages[q["source"]].add(q["page"])
                    
                    if user_ans == q["correct"]:
                        st.success("✅ **Correct!**")
                        st.markdown(f"**Explanation:** {q['explanation']}")
                    else:
                        st.error(f"❌ **Incorrect.** The correct answer was **{q['correct']}**.")
                        st.markdown(f"**Explanation:** {q['explanation']}")
                        
                        # Save to mistakes log
                        st.session_state.mistake_log.append({
                            "Date": datetime.now().strftime("%Y-%m-%d"),
                            "Domain": domain_choice,
                            "Question": q["question"],
                            "Your Answer": user_ans,
                            "Correct Answer": q["correct"],
                            "Source": f"{q['source']} (Page {q['page']})"
                        })
                else:
                    st.warning("Please select an option first.")

# --- TAB 2: % COVERAGE TRACKER ---
with tab_progress:
    st.subheader("📈 Verified Page & Topic Coverage")
    st.write("This calculates exact percentage coverage based on pages the AI has quizzed you on:")
    if not st.session_state.pdf_texts:
        st.caption("No sources loaded yet.")
    else:
        for fname, pages in st.session_state.pdf_texts.items():
            total_pages = len(pages)
            covered = len(st.session_state.covered_pages[fname])
            pct = int((covered / total_pages) * 100) if total_pages > 0 else 0
            
            st.markdown(f"**{fname}**")
            st.progress(pct / 100.0)
            st.caption(f"Actively tested on **{covered}** out of **{total_pages}** pages (**{pct}% Covered**)")
            st.markdown("---")

# --- TAB 3: MISTAKE LOG ---
with tab_mistakes:
    st.subheader("🧠 Logged Weak Areas")
    if not st.session_state.mistake_log:
        st.success("No mistakes recorded yet! Take some quizzes or log external ones.")
    else:
        st.write(f"You have **{len(st.session_state.mistake_log)}** mistakes logged:")
        for idx, m in enumerate(reversed(st.session_state.mistake_log)):
            with st.expander(f"❌ {m['Domain']}: {m['Question'][:40]}..."):
                st.write(f"**Q:** {m['Question']}")
                st.write(f"**You Answered:** :red[{m['Your Answer']}]")
                st.write(f"**Correct:** :green[{m['Correct Answer']}]")
                st.caption(f"Source: {m['Source']} | Logged: {m['Date']}")
        if st.button("Clear Log"):
            st.session_state.mistake_log = []
            st.rerun()

# --- TAB 4: EXTERNAL QUESTIONS ---
with tab_ext:
    st.subheader("➕ Log External Practice Mistakes")
    st.caption("Did you miss a question on Boson or InfoSecTrain? Save it here:")
    with st.form("ext_form", clear_on_submit=True):
        ext_dom = st.selectbox("Domain:", [f"Domain {i}" for i in range(1, 9)])
        ext_q = st.text_area("Question:")
        ext_wrong = st.text_input("Your Wrong Choice:")
        ext_right = st.text_input("Correct Answer:")
        ext_src = st.text_input("Source/Test Name:")
        if st.form_submit_button("Save to Mistake Log", use_container_width=True) and ext_q and ext_right:
            st.session_state.mistake_log.append({
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Domain": ext_dom,
                "Question": ext_q,
                "Your Answer": ext_wrong or "N/A",
                "Correct Answer": ext_right,
                "Source": ext_src or "External Practice"
            })
            st.success("Saved directly to your Mistake Log!")
