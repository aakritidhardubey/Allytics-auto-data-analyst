import streamlit as st
import pandas as pd
import hashlib
from PIL import Image
from pandasai import Agent
from llms.groq_llm import GroqLLM
from utils.auth import hash_password, verify_password
from utils.db import (
    register_user, authenticate_user,
    save_user_session, load_user_session
)

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "login"
if "file_sessions" not in st.session_state:
    st.session_state.file_sessions = {}
if "current_file_id" not in st.session_state:
    st.session_state.current_file_id = None

def get_file_id(uploaded_file):
    if uploaded_file is not None:
        file_content = uploaded_file.read()
        uploaded_file.seek(0)
        return hashlib.md5(f"{uploaded_file.name}{len(file_content)}".encode()).hexdigest()[:8]
    return None

def clean_column_names(df):
    df.columns = df.columns.str.replace(r'[()"\']', '', regex=True)
    df.columns = df.columns.str.replace(r'\s+', '_', regex=True)
    df.columns = df.columns.str.strip()
    return df

def show_login():
    st.set_page_config(page_title="Login - Allytics", layout="centered")
    st.markdown("""
        <style>
            div.block-container {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 90vh;
            }
            .stButton > button {
                border-radius: 8px;
                padding: 0.5rem 1rem;
                font-size: 16px;
                background-color: #007ACC;
                color: white;
            }
            .stButton > button:hover {
                background-color: #005fa3;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("Login to Allytics")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.name = user["name"]
            st.session_state.file_sessions = load_user_session(username)
            st.session_state.page = "main"
            st.rerun()
        else:
            st.error("Invalid username or password")

    if st.button("Go to Register"):
        st.session_state.page = "register"
        st.rerun()

def show_register():
    st.set_page_config(page_title="Register - Allytics", layout="centered")
    st.markdown("""
        <style>
            div.block-container {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 90vh;
            }
            .stButton > button {
                border-radius: 8px;
                padding: 0.5rem 1rem;
                font-size: 16px;
                background-color: #28a745;
                color: white;
            }
            .stButton > button:hover {
                background-color: #1e7e34;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("Register to Allytics")
    name = st.text_input("Name")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        if register_user(username, password, name):
            st.success("Registration successful. Please log in.")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error("Username already exists.")

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

def show_main_app():
    st.set_page_config(page_title="Allytics", layout="wide")

    st.markdown("""
        <style>
            .top-bar {
                display: flex;
                justify-content: flex-end;
                padding-right: 1.5rem;
                margin-bottom: -2rem;
            }
            .logout-btn button {
                border-radius: 8px;
                background-color: #dc3545;
                color: white;
                font-weight: 500;
                padding: 0.5rem 1rem;
            }
            .logout-btn button:hover {
                background-color: #a71d2a;
            }
            .title-container {
                text-align: center;
                margin-top: -40px;
            }
            .title-container h1 {
                font-size: 34px;
                color: #00BFFF;
                margin-bottom: 0;
            }
            .title-container p {
                font-size: 16px;
                color: #bbb;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<div class='top-bar logout-btn'>" + 
                st.button("Logout", key="logout") * "" + "</div>", 
                unsafe_allow_html=True)

    if st.session_state.get("logout"):
        save_user_session(st.session_state.username, st.session_state.file_sessions)
        st.session_state.clear()
        st.session_state.page = "login"
        st.rerun()

    st.markdown("""
        <div class="title-container">
            <h1>🤖 Allytics</h1>
            <p>Upload. Ask. Analyze.</p>
        </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        top = st.container()
        bottom = st.container()

        with top:
            st.markdown("## Your Files")
            uploaded_file = st.file_uploader("Upload files", type=["csv"])

            if uploaded_file:
                file_id = get_file_id(uploaded_file)
                if file_id not in st.session_state.file_sessions:
                    df = pd.read_csv(uploaded_file)
                    df = clean_column_names(df)
                    st.session_state.file_sessions[file_id] = {
                        "name": uploaded_file.name,
                        "df": df,
                        "agent": None,
                        "chat_history": []
                    }
                st.session_state.current_file_id = file_id

            st.markdown("### Session Files")
            for fid, session in st.session_state.file_sessions.items():
                if st.button(session["name"], key=f"switch_{fid}"):
                    st.session_state.current_file_id = fid

            if st.session_state.current_file_id and st.button("🗑️"):
                del st.session_state.file_sessions[st.session_state.current_file_id]
                st.session_state.current_file_id = next(iter(st.session_state.file_sessions), None)
                st.rerun()

        with bottom:
            if st.session_state.current_file_id and st.button("🧹 Clear Chat"):
                st.session_state.file_sessions[st.session_state.current_file_id]["chat_history"] = []
                st.rerun()

    if st.session_state.current_file_id:
        current = st.session_state.file_sessions[st.session_state.current_file_id]
        df = current["df"]
        st.subheader(current['name'])

        if st.checkbox("Show Data Preview"):
            st.dataframe(df)
            st.write(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")

        if current["agent"] is None:
            current["agent"] = Agent(df, config={
                "llm": GroqLLM(),
                "conversational": True,
                "verbose": False,
                "enable_cache": False,
                "custom_instructions": """
                Always provide clear, conversational answers.
                When showing data results:
                1. Start with a direct answer
                2. Add interesting insights
                3. Avoid raw data dumps
                """
            })

        st.write("### Ask Allytics Anything")
        for q, a in current["chat_history"]:
            with st.chat_message("user"):
                st.markdown(q)
            with st.chat_message("assistant"):
                st.markdown(a)

        question = st.chat_input("Type a question...")
        if question:
            answer = current["agent"].chat(question)
            current["chat_history"].append((question, answer))
            st.rerun()
    else:
        st.info("Upload and select a CSV file to begin using Allytics.")

if st.session_state.page == "login":
    show_login()
elif st.session_state.page == "register":
    show_register()
elif st.session_state.page == "main":
    if st.session_state.authenticated:
        show_main_app()
    else:
        st.session_state.page = "login"
        st.rerun()
