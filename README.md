# Modular Calendar AI Application

This is a modular and extensible AI-powered calendar web application built with Flask, MongoDB, and an integrated LLM (e.g., LLaMA via Ollama). It supports authentication, event creation, viewing, AI-based assistance, and recurring events.

---

## 🚀 Features

- User Authentication (Login, Register)
- Month View Calendar with Navigation
- Event Management (CRUD)
- Recurring Events Support
- AI Assistant to process natural language calendar requests
- Clean MVC-like structure with modular components

---

## 🗂 Project Structure

```
├── .env
├── .gitignore
├── app
│   ├── __init__.py
│   ├── config
│   │   └── config.py
│   ├── models
│   ├── routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── main.py
│   ├── services
│   │   ├── __init__.py
│   │   └── ai_assistant.py
│   ├── static
│   │   ├── css
│   │   │   ├── style.css
│   │   │   └── styles.css
│   │   ├── img
│   │   │   └── favicon.ico
│   │   └── js
│   │       └── script.js
│   │       └── todo.js
│   ├── templates
│   │   ├── change_password.html
│   │   ├── index.html
│   │   ├── login.html
│   │   └── signup.html
│   └── utils
│       └── enums.py
├── requirements.txt
└── run.py
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/calendar-ai.git
cd calendar-ai
```

### 2. Set up a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create a `.env` file in the root directory with content like:

```bash
SECRET_KEY=your_secret_key
MONGO_URI=mongodb://localhost:27017/calendar_ai
OLLAMA_MODEL_NAME=llama3.2
OLLAMA_API_URL=http://localhost:11434/api/generate
```

### 5. Run the application

```bash
python run.py
```

Access the app at `http://127.0.0.1:5000/`.

---

## 🧠 AI Integration

The app communicates with a local Ollama server to process calendar-related natural language requests. You can adapt the `llm_service.py` for OpenAI or other APIs.

---

## 📂 Contributions

PRs are welcome. Please follow PEP8 and modular design guidelines.

---

## 🛡 License

MIT License. See LICENSE for details.
