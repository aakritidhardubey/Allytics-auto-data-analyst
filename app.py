import os
import streamlit as st
import pandas as pd
import hashlib
import uuid
import tempfile
import json
import io
import base64
from PIL import Image
from pandasai import Agent
from llms.groq_llm import GroqLLM
from utils.auth import hash_password, verify_password
from utils.db import register_user, authenticate_user, save_user_session, load_user_session
import plotly.express as px
import plotly.graph_objects as go
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Initialize session state
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

def convert_chart_to_base64(answer):
    """Convert chart to base64 string for reliable storage"""
    try:
        if isinstance(answer, go.Figure):
            # Convert plotly figure to base64 image
            img_bytes = answer.to_image(format="png", width=800, height=600)
            img_base64 = base64.b64encode(img_bytes).decode()
            return {"type": "base64_image", "data": img_base64}
        elif isinstance(answer, Figure):
            # Convert matplotlib figure to base64 image
            buf = io.BytesIO()
            answer.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode()
            buf.close()
            return {"type": "base64_image", "data": img_base64}
    except Exception as e:
        st.warning(f"Could not convert chart: {e}")
        return {"type": "text", "content": "Chart conversion failed"}
    return None

def process_and_store_answer(answer):
    """Process answer and return appropriate storage format"""
    # Handle chart objects
    if isinstance(answer, (go.Figure, Figure)):
        return convert_chart_to_base64(answer)
    
    # Handle existing image files
    elif isinstance(answer, str) and os.path.exists(answer) and answer.lower().endswith((".png", ".jpg", ".jpeg")):
        try:
            with open(answer, "rb") as f:
                img_data = f.read()
                img_base64 = base64.b64encode(img_data).decode()
                return {"type": "base64_image", "data": img_base64}
        except:
            return {"type": "text", "content": "Image load failed"}
    
    # Handle text responses
    else:
        return {"type": "text", "content": str(answer)}

def display_stored_answer(stored_answer, index):
    """Display answer based on its stored format"""
    if isinstance(stored_answer, dict):
        if stored_answer["type"] == "base64_image":
            try:
                # Display base64 image
                st.image(
                    f"data:image/png;base64,{stored_answer['data']}", 
                    caption=f"Chart #{index+1}", 
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Failed to display chart: {e}")
        elif stored_answer["type"] == "text":
            st.markdown(stored_answer["content"])
        elif stored_answer["type"] == "plotly_json":
            try:
                fig = go.Figure(json.loads(stored_answer["data"]))
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.error("Failed to display chart")
    else:
        # Legacy format handling - convert to new format
        if isinstance(stored_answer, str) and os.path.exists(stored_answer) and stored_answer.lower().endswith((".png", ".jpg", ".jpeg")):
            try:
                with open(stored_answer, "rb") as f:
                    img_data = f.read()
                    img_base64 = base64.b64encode(img_data).decode()
                    st.image(f"data:image/png;base64,{img_base64}", caption=f"Chart #{index+1}", use_container_width=True)
            except:
                st.error("Failed to load legacy image")
        elif isinstance(stored_answer, go.Figure):
            # Convert legacy plotly figure to base64 and display
            converted = convert_chart_to_base64(stored_answer)
            if converted and converted["type"] == "base64_image":
                st.image(f"data:image/png;base64,{converted['data']}", caption=f"Chart #{index+1}", use_container_width=True)
            else:
                st.plotly_chart(stored_answer, use_container_width=True)
        elif isinstance(stored_answer, Figure):
            # Convert legacy matplotlib figure to base64 and display
            converted = convert_chart_to_base64(stored_answer)
            if converted and converted["type"] == "base64_image":
                st.image(f"data:image/png;base64,{converted['data']}", caption=f"Chart #{index+1}", use_container_width=True)
            else:
                st.pyplot(stored_answer)
        else:
            st.markdown(str(stored_answer))

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
                st.session_state.file_sessions[file_id] = {
                    "name": uploaded_file.name, 
                    "df": df, 
                    "agent": None, 
                    "chat_history": []
                }
            st.session_state.current_file_id = file_id

        st.markdown("### Your Files")
        for fid, session in st.session_state.file_sessions.items():
            for other_fid in list(st.session_state.file_sessions.keys()):
                if other_fid != fid:
                    st.session_state[f"menu_open_{other_fid}"] = False

            menu_col, icon_col = st.columns([8, 1])

            with menu_col:
                file_label = f" {session['name']}"
                st.markdown(f'<div class="file-entry">{file_label}</div>', unsafe_allow_html=True)
                if st.button("Load", key=f"load_{fid}"):
                    st.session_state.current_file_id = fid
                    st.rerun()

            with icon_col:
                if st.button("⋮", key=f"menu_toggle_{fid}"):
                    current_state = st.session_state.get(f"menu_open_{fid}", False)
                    for k in list(st.session_state.file_sessions.keys()):
                        st.session_state[f"menu_open_{k}"] = False
                    st.session_state[f"menu_open_{fid}"] = not current_state

            if st.session_state.get(f"menu_open_{fid}", False):
                st.warning("Are you sure you want to delete this file?")
                confirm_col1, confirm_col2 = st.columns([1, 1])
                with confirm_col1:
                    if st.button(" Yes, delete", key=f"confirm_yes_{fid}"):
                        del st.session_state.file_sessions[fid]
                        if st.session_state.current_file_id == fid:
                            st.session_state.current_file_id = next(iter(st.session_state.file_sessions), None)
                        st.session_state.pop(f"menu_open_{fid}", None)
                        st.rerun()
                with confirm_col2:
                    if st.button("Cancel", key=f"confirm_no_{fid}"):
                        st.session_state.pop(f"menu_open_{fid}", None)
                        st.rerun()

        if st.session_state.current_file_id and st.button("Clear Chat"):
            st.session_state.file_sessions[st.session_state.current_file_id]["chat_history"] = []
            st.rerun()

    if st.session_state.current_file_id:
        current = st.session_state.file_sessions[st.session_state.current_file_id]
        df = current["df"]
        st.subheader(current['name'])

        if st.checkbox("Show Data Preview"):
            st.dataframe(df)
            st.write(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
        
        if st.checkbox("Show Graph"):
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
        st.write(f"🧠 Chat History: {len(current['chat_history'])} entries")

        # Display chat history
        for i, (q, a) in enumerate(current["chat_history"]):
            with st.chat_message("user"):
                st.markdown(q)
            with st.chat_message("assistant"):
                st.write(f"↪️ Response #{i+1}")
                display_stored_answer(a, i)

        # Chat input handling
        question = st.chat_input("Type a question...")
        if question:
            prev_q = current["chat_history"][-1][0] if current["chat_history"] else None
            if prev_q == question:
                st.warning("This question was just asked.")
                st.stop()

            try:
                answer = current["agent"].chat(question)
                
                processed_answer = process_and_store_answer(answer)
                
                # Clear any matplotlib figures to prevent memory leaks
                if isinstance(answer, Figure):
                    plt.close(answer)
                
                current["chat_history"].append((question, processed_answer))
                
                # Update session state
                st.session_state.file_sessions[st.session_state.current_file_id] = current
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Agent error: {e}")
                st.stop()

    else:
        st.info("Upload and select a CSV file to begin using Allytics.")

# Main app routing
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