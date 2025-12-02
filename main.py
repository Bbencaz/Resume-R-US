import streamlit as st
import PyPDF2
import io
import os
from  openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Resume R US", page_icon="📄", layout="centered")

# ---------- VISUAL STYLING ONLY (NO LOGIC CHANGED) ----------
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
        background: #000000;
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

# ---------- HERO (CENTERED) ----------
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

# ---------- INSTRUCTIONS ----------
st.markdown(
    """
    <div class="how-it-works">
        <strong>How it works:</strong><br><br>
        1. Upload your resume<br>
        2. (Optional) Tell us your target job<br>
        3. Click analyze
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- INPUT SECTION ----------
st.markdown('<div class="upload-card">', unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "txt"])
job_role = st.text_input("Enter the job role you're targetting (optional)")
analyze = st.button("✨ Analyze My Resume", use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------- FILE EXTRACTION (UNCHANGED) ----------
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


# ---------- AI ANALYSIS (UNCHANGED LOGIC) ----------
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

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        with st.spinner("Analyzing your resume..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", 
                     "content": "You are an expert resume reviewer with years of HR and recruitment experience."},
                    {"role": "user", "content": prompt}
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
