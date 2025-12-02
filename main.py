import streamlit as st
import PyPDF2
import io
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Resume R US", page_icon="📄", layout="centered")

st.title("Resume R US")
st.markdown("Upload your resume and get AI-powered suggestions to improve it!")

OPEN_AI_API_KEY = os.getenv("OPENAI_API_KEY")

# -------------------------
# ACCOUNT / AUTH SETUP
# -------------------------

# Initialize user store (simple in-memory "database")
# You can remove the default user if you want
if "users" not in st.session_state:
    st.session_state.users = {
        "user": "password123"  # default demo account
    }

# Initialize login state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# -------------------------
# SIDEBAR: LOGIN / SIGNUP / LOGOUT
# -------------------------
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
        # Choose between Login and Create Account
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
                    # Save new user
                    st.session_state.users[new_username] = new_password
                    st.success("Account created! You can now log in.")
                    # Optionally auto-login:
                    # st.session_state.logged_in = True
                    # st.session_state.current_user = new_username
                    # st.rerun()

# -------------------------
# BLOCK APP IF NOT LOGGED IN
# -------------------------
if not st.session_state.logged_in:
    st.info("Please log in or create an account in the sidebar to use the app.")
    st.stop()

# -------------------------
# MAIN APP (ONLY AFTER LOGIN)
# -------------------------

uploaded_file = st.file_uploader("Upload Resume", type=["pdf", "txt"])
job_role = st.text_input("Enter the job role you're targeting (optional)")

analyze = st.button("Analyze Resume")


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

        st.markdown("### Analysis Results:")
        st.markdown(response.choices[0].message.content)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
