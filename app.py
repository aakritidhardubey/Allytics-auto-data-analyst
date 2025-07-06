import os
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
import plotly.express as px
from matplotlib.figure import Figure
import plotly.graph_objects as go

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
    if st.button("Logout", key="logout"):
        save_user_session(st.session_state.username, st.session_state.file_sessions)
        st.session_state.clear()
        st.session_state.page = "login"
        st.rerun()

    st.title("🤖 Allytics - Upload. Ask. Analyze.")

    with st.sidebar:
        st.header("Your Files")
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded_file:
            file_id = get_file_id(uploaded_file)
            if file_id not in st.session_state.file_sessions:
                df = clean_column_names(pd.read_csv(uploaded_file))
                st.session_state.file_sessions[file_id] = {"name": uploaded_file.name, "df": df, "agent": None, "chat_history": []}
            st.session_state.current_file_id = file_id

        for fid, session in st.session_state.file_sessions.items():
            if st.button(session["name"], key=f"switch_{fid}"):
                st.session_state.current_file_id = fid

        if st.session_state.current_file_id and st.button("🗑️ Delete Current File"):
            del st.session_state.file_sessions[st.session_state.current_file_id]
            st.session_state.current_file_id = next(iter(st.session_state.file_sessions), None)
            st.rerun()

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
        
        if st.checkbox(" Show Graph "):
            graph_type = st.selectbox("Select Graph Type", ["Line", "Bar", "Histogram", "Boxplot", "Scatter"])
            numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
            all_columns = df.columns.tolist()

            if graph_type in ["Line", "Bar", "Scatter", "Boxplot"]:
                x_axis = st.selectbox("X-axis", options=all_columns)
                y_axis = st.selectbox("Y-axis", options=numeric_columns)
            elif graph_type == "Histogram":
                x_axis = st.selectbox("Column", options=numeric_columns)
                y_axis = None

            if st.button("Generate Graph"):
                st.write(f"### {graph_type} Plot")
                try:
                    fig = None
                    if graph_type == "Line":
                        fig = px.line(df, x=x_axis, y=y_axis)
                    elif graph_type == "Bar":
                        fig = px.bar(df, x=x_axis, y=y_axis)
                    elif graph_type == "Histogram":
                        fig = px.histogram(df, x=x_axis)
                    elif graph_type == "Boxplot":
                        fig = px.box(df, x=x_axis, y=y_axis)
                    elif graph_type == "Scatter":
                        fig = px.scatter(df, x=x_axis, y=y_axis)

                    st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Error generating graph: {e}")


        if current["agent"] is None:
            current["agent"] = Agent(df, config={
                "llm": GroqLLM(),
                "conversational": True,
                "verbose": False,
                "enable_cache": False,
                "custom_instructions": """
                Always provide clear, conversational answers.
                Avoid raw data dumps. Prefer names, summaries, and charts.
                """
            })

        st.write("### Ask Allytics Anything")
        for q, a in current["chat_history"]:
            with st.chat_message("user"):
                st.markdown(q)
            with st.chat_message("assistant"):
                if isinstance(a, go.Figure):
                    st.plotly_chart(a, use_container_width=True)
                elif isinstance(a, Figure):
                    st.pyplot(a)
                elif isinstance(a, str)and os.path.exists(a)  and a.lower().endswith((".png", ".jpg", ".jpeg")):
                    st.image(a, caption="Generated Chart", use_container_width=True)
                else:
                    st.markdown(a)

        question = st.chat_input("Type a question...")
        if question:
            if not current["chat_history"] or current["chat_history"][-1][0] != question:
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
