import streamlit as st
import PyPDF2
import io
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Resume R US", page_icon="📄", layout="centered")

# =========================================
#  UI STYLING (GRADIENT + HERO + CARDS)
# =========================================
st.markdown(
    """
    <style>
    /* Midnight blue gradient background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    }

    /* Centered hero container */
    .hero-container {
        max-width: 800px;
        margin: 2.5rem auto 1.5rem auto;
        text-align: center;
    }

    /* Pill (badge) */
    .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: #ffffff;
        color: #000000;
        border-radius: 999px;
        padding: 0.35rem 0.9rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.9rem;
        border: 1px solid #e2e8f0;
    }

    .pill span.emoji {
        font-size: 1rem;
        color: #000000;
    }

    /* BIG centered title */
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.4rem;
        color: #f9fafb;  /* almost white */
    }

    /* Subtitle on background */
    .hero-subtitle {
        font-size: 1.05rem;
        color: #e5e7eb;
        margin-bottom: 1.6rem;
    }

    /* "How it works" text */
    .how-it-works {
        max-width: 800px;
        margin: 0 auto 1rem auto;
        color: #e5e7eb;
        font-size: 0.95rem;
        text-align: center;
    }


    /* Analysis output card */
    .analysis-card {
        max-width: 800px;
        margin: 1.5rem auto 0 auto;
        padding: 1.2rem 1.4rem;
        border-radius: 1rem;
        background: #fefce8;
        border: 1px solid #facc15;
        color: #000000 !important;
    }

    .footer-note {
        font-size: 0.75rem;
        color: #e5e7eb;
        margin-top: 1.5rem;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

OPEN_AI_API_KEY = os.getenv("OPENAI_API_KEY")

# =========================================
#  HERO + HOW IT WORKS (ALWAYS VISIBLE)
# =========================================
st.markdown(
    """
    <div class="hero-container">
        <div class="pill">
            <span class="emoji">⚡</span>
            <span>AI Resume Feedback</span>
        </div>
        <div class="hero-title">Resumes R US</div>
        <div class="hero-subtitle">
            Upload your resume and receive clear, personalized suggestions to make it stronger and more job-ready.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="how-it-works">
        <strong>How it works:</strong><br><br>
        1. Create an account or log in from the sidebar<br>
        2. Upload your resume<br>
        3. (Optional) Tell us your target job<br>
        4. Click analyze
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================
#  ACCOUNT / AUTH SETUP (SIDEBAR)
# =========================================

# Simple in-memory "user database"
if "users" not in st.session_state:
    st.session_state.users = {
        "user": "password123"  # default demo account
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

with st.sidebar:
    st.header("Account")

    if st.session_state.logged_in:
        st.markdown(f"**Logged in as:** `{st.session_state.current_user}`")
        logout_clicked = st.button("Log out")

        if logout_clicked:
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.success("You have been logged out.")
            st.rerun()
    else:
        auth_mode = st.radio("Account options", ["Login", "Create Account"])

        if auth_mode == "Login":
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_clicked = st.button("Login")

            if login_clicked:
                users = st.session_state.users
                if username in users and users[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        elif auth_mode == "Create Account":
            st.subheader("Create Account")
            new_username = st.text_input("New username")
            new_password = st.text_input("New password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            create_clicked = st.button("Create Account")

            if create_clicked:
                if not new_username or not new_password:
                    st.error("Username and password cannot be empty.")
                elif new_username in st.session_state.users:
                    st.error("Username already exists. Please choose another one.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    st.session_state.users[new_username] = new_password
                    st.success("Account created! You can now log in.")

# Block main app if not logged in
if not st.session_state.logged_in:
    st.info("Please log in or create an account in the sidebar to upload and analyze your resume.")
    st.stop()

# =========================================
#  MAIN APP (ONLY AFTER LOGIN)
# =========================================

# Upload + inputs inside styled card
st.markdown('<div class="upload-card">', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "txt"])
job_role = st.text_input("Enter the job role you're targetting (optional)")
analyze = st.button("✨ Analyze My Resume", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------- FILE EXTRACTION ----------
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text


def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    return uploaded_file.read().decode("utf-8")


# ---------- AI ANALYSIS ----------
if analyze and uploaded_file:
    try:
        file_content = extract_text_from_file(uploaded_file)

        if not file_content.strip():
            st.error("File does not have any content...")
            st.stop()

        prompt = f"""
Please analyze this resume and provide constructive feedback.

Focus on the following aspects:
1. Content clarity and impact
2. Skills presentation
3. Experience descriptions
4. Specific improvements for {job_role if job_role else 'general job applications'}

Resume content:
{file_content}

Please provide your analysis in a clear, structured format with specific recommendations.
"""

        client = OpenAI(api_key=OPEN_AI_API_KEY)

        with st.spinner("Analyzing your resume..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert resume reviewer with years of HR and recruitment experience.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

        st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Analysis Results:")
        st.markdown(response.choices[0].message.content)
        st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

# ---------- FOOTER ----------
st.markdown(
    '<div class="footer-note">Your resume is processed securely and never stored.</div>',
    unsafe_allow_html=True,
)

