# 🤖 Allytics

**Allytics** is a smart, interactive data analytics chatbot. Upload CSV files, ask natural language questions, and get insights instantly using an LLM-powered interface — all in a clean, user-authenticated Streamlit app.

## 🚀 Features

* 🔐 **User Authentication** (MongoDB Atlas-backed)
* 📂 Upload multiple CSV files & persist sessions
* 🧠 Ask natural-language questions (via PandasAI + Groq LLM)
* 💬 Chat history stored and reloaded per user
* 📉 Interactive visualizations with Plotly & Matplotlib
* 🧹 One-click clear chat & file deletion
* 📊 Data preview, file switching, and chart selection

## 🧰 Tech Stack

| Layer | Tools Used |
|-------|------------|
| **Frontend/UI** | Streamlit |
| **Backend** | Python, PandasAI Assistant |
| **AI/LLM** | PandasAI + Groq LLM |
| **Database** | MongoDB Atlas |
| **Authentication** | bcrypt, Python dotenv |
| **Visualizations** | Plotly, Matplotlib |

## 🧑‍💻 Installation

### 1. Clone the repository

```bash
git clone https://github.com/aakritidhardubey/Allytics-auto-data-analyst.git
cd Allytics-auto-data-analyst
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your `.env` file

Create a `.env` file with your MongoDB URI and any other secrets:

```ini
MONGO_URI=your_mongo_uri
GROQ_API_KEY=your_groq_api_key
```

### 5. Run the app

```bash
streamlit run app.py
```

## 📝 How It Works

1. **Register/Login**: Users create an account or sign in to access their personalized dashboard
2. **Upload CSV**: Upload any CSV file to begin analysis
3. **Preview Data**: View your data structure and basic statistics
4. **Ask Questions**: Use natural language to query your data, such as:
   - "What's the average revenue by month?"
   - "Show a bar chart of product sales."
   - "Which category has the highest profit margin?"
5. **Get Insights**: Allytics processes your question via LLM and generates summaries, charts, or detailed analysis
6. **Save & Resume**: Your chat history and uploaded files are saved for future sessions

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [PandasAI](https://github.com/gventuri/pandas-ai) for the natural language data analysis
- [Groq](https://groq.com/) for fast LLM inference
- [Streamlit](https://streamlit.io/) for the beautiful web interface
- [MongoDB Atlas](https://www.mongodb.com/atlas) for cloud database services

## 📞 Contact

**Aakriti Dhar Dubey** - [GitHub](https://github.com/aakritidhardubey)

Project Link: [https://github.com/aakritidhardubey/Allytics-auto-data-analyst](https://github.com/aakritidhardubey/Allytics-auto-data-analyst)

---

⭐ **Star this repo if you found it helpful!**