# 🤖 Allytics

**Allytics** is a smart, interactive data analytics chatbot. Upload CSV files, ask natural language questions, and get insights instantly using an LLM-powered interface — all in a clean, user-authenticated Streamlit app.

---

## 🚀 Features

- 🔐 **User Authentication** (MongoDB Atlas-backed)
- 📂 Upload multiple CSV files & persist sessions
- 🧠 Ask natural-language questions (via [PandasAI](https://github.com/gventuri/pandas-ai) + [Groq LLM](https://groq.com/))
- 💬 Chat history stored and reloaded per user
- 🧹 One-click clear chat
- 📉 Data preview, file switching & deletion

---

## 📦 Tech Stack

- **Frontend/UI**: Streamlit
- **Database**: MongoDB Atlas
- **LLM Interface**: PandasAI + Groq LLM wrapper
- **Auth & Security**: bcrypt, Python dotenv
- **Backend**: Python, Pandas

---

## 🧑‍💻 Installation

1. **Clone this repo**:

   ```bash
   git clone https://github.com/aakritidhardubey/Allytics-auto-data-analyst.git
   cd Allytics-auto-data-analyst

