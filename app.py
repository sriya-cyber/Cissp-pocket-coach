import streamlit as st
import pandas as pd
from datetime import datetime

# Page Configuration for Mobile Response
st.set_page_config(page_title="CISSP Pocket Coach", page_icon="🛡️", layout="centered")

# Initialize Session State for Data Storage
if 'sources' not in st.session_state:
    # Starting with your first book pre-configured
    st.session_state.sources = {
        "Memory Palace 5th Ed (Prashant Mohan)": {"total_topics": 150, "covered_topics": set()}
    }
if 'mistake_log' not in st.session_state:
    st.session_state.mistake_log = []
if 'custom_questions' not in st.session_state:
    st.session_state.custom_questions = []

st.title("🛡️ CISSP Pocket Coach")
st.caption("Low-friction, mobile-first review tailored to your schedule.")

# Top Navigation Tabs
tab_quiz, tab_progress, tab_mistakes, tab_add_external = st.tabs([
    "🎯 Quick Quiz", "📊 % Coverage", "🧠 Mistake Log", "➕ Add External Q"
])

# --- TAB 1: QUICK QUIZ ---
with tab_quiz:
    st.subheader("5-Minute Review Session")
    selected_source = st.selectbox("Select Study Source:", list(st.session_state.sources.keys()))
    domain = st.selectbox("Select Domain:", [f"Domain {i}" for i in range(1, 9)] + ["Mixed Domains"])
    
    # Mock question representation (In full deployment, this connects to your PDF extractor/LLM engine)
    st.markdown("---")
    st.markdown(f"**Source:** *{selected_source}* | **Topic #14:** Asset Classification")
    st.write("Which data classification role is ultimately responsible for defining data sensitivity and authorization tiers?")
    
    user_choice = st.radio("Choose your answer:", [
        "A) Data Custodian",
        "B) Data Owner",
        "C) System Owner",
        "D) Security Administrator"
    ], index=None)
    
    if st.button("Submit Answer", use_container_width=True):
        if user_choice:
            # Mark topic as covered for percentage calculation
            st.session_state.sources[selected_source]["covered_topics"].add(14)
            
            if "B) Data Owner" in user_choice:
                st.success("✅ **Correct!** The Data Owner (usually a senior business unit manager) is ultimately liable and defines classification.")
                st.info("💡 *Source Citation: Memory Palace 5th Ed, Domain 2, Page 25.*")
            else:
                st.error("❌ **Incorrect.** You selected a role responsible for implementation or maintenance rather than ultimate liability.")
                st.markdown("**Explanation:** The **Data Owner** bears ultimate responsibility and decides classification. The **Data Custodian** executes routine backups and applies technical access controls based on the Owner's policy.")
                st.info("💡 *Source Citation: Memory Palace 5th Ed, Domain 2, Page 25.*")
                
                # Log Mistake
                st.session_state.mistake_log.append({
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Domain": domain,
                    "Question": "Which data classification role is ultimately responsible for defining data sensitivity?",
                    "Your Answer": user_choice,
                    "Correct Answer": "B) Data Owner",
                    "Source": f"{selected_source} (p. 25)"
                })
        else:
            st.warning("Please select an option first.")

# --- TAB 2: % COVERAGE TRACKER ---
with tab_progress:
    st.subheader("📈 Syllabus & Source Coverage")
    st.write("See exactly how much of each document you've actively reviewed through quizzing:")
    
    for src_name, data in st.session_state.sources.items():
        covered_count = len(data["covered_topics"])
        total_count = data["total_topics"]
        pct = int((covered_count / total_count) * 100) if total_count > 0 else 0
        
        st.markdown(f"**{src_name}**")
        st.progress(pct / 100.0)
        st.caption(f"Covered **{covered_count}** of **{total_count}** core concepts/pages (**{pct}%**)")
        st.markdown("---")
        
    st.info("💡 *Tip: Adding new PDFs or sources in the future will automatically add a new progress bar here.*")

# --- TAB 3: MISTAKE LOG ---
with tab_mistakes:
    st.subheader("🧠 Logged Weak Spots")
    if not st.session_state.mistake_log:
        st.success("No mistakes logged yet! Take a quick quiz or add external mistakes.")
    else:
        st.write(f"You have **{len(st.session_state.mistake_log)}** items flagged for review:")
        for idx, item in enumerate(reversed(st.session_state.mistake_log)):
            with st.expander(f"❌ {item['Domain']}: {item['Question'][:45]}..."):
                st.write(f"**Question:** {item['Question']}")
                st.write(f"**You Answered:** :red[{item['Your Answer']}]")
                st.write(f"**Correct Answer:** :green[{item['Correct Answer']}]")
                st.caption(f"Source: {item['Source']} | Logged on: {item['Date']}")
        if st.button("Clear Log (After Reviewing)"):
            st.session_state.mistake_log = []
            st.rerun()

# --- TAB 4: ADD EXTERNAL QUESTIONS ---
with tab_add_external:
    st.subheader("➕ Add External Practice Mistakes")
    st.write("Tried questions on Boson, InfoSecTrain, or PocketPrep? Log them here so they stay in your review loop:")
    
    with st.form("ext_q_form", clear_on_submit=True):
        ext_domain = st.selectbox("Domain:", [f"Domain {i}" for i in range(1, 9)])
        ext_q = st.text_area("Question Text:")
        ext_wrong = st.text_input("What you answered incorrectly:")
        ext_correct = st.text_input("The Correct Answer:")
        ext_src = st.text_input("Source (e.g., Boson Exam A, Q42):")
        
        submitted = st.form_submit_button("Save to Mistake Log", use_container_width=True)
        if submitted and ext_q and ext_correct:
            st.session_state.mistake_log.append({
                "Date": datetime.now().strftime("%Y-%m-%d"),
                "Domain": ext_domain,
                "Question": ext_q,
                "Your Answer": ext_wrong if ext_wrong else "N/A",
                "Correct Answer": ext_correct,
                "Source": ext_src if ext_src else "External Practice"
            })
            st.success("Saved to your Mistake Log!")
