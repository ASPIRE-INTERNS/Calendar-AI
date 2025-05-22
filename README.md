# Modular Calendar AI Application

This is a modular and extensible AI-powered calendar web application built with Flask, MongoDB, and an integrated LLM (e.g., LLaMA via Ollama). It supports authentication, event creation, viewing, AI-based assistance, and recurring events.

---

## 🚀 Features

- User Authentication (Login, Register)
- Month View Calendar with Navigation
- Event Management (CRUD)
- Recurring Events Support
- AI Assistant to process natural language calendar requests
- To-Do List Management
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
│   │   ├── img
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

```sh
git clone https://github.com/yourusername/calendar-ai.git
cd calendar-ai
```

### 2. Install Python

- Download Python 3.11+ from the [official website](https://www.python.org/downloads/).
- Make sure to check "Add Python to PATH" during installation.

### 3. Install MongoDB

- Download MongoDB Community Server from the [official MongoDB download page](https://www.mongodb.com/try/download/community).
- Follow the [MongoDB installation guide](https://docs.mongodb.com/manual/installation/) for your OS.
- After installation, start the MongoDB server:
  - **Windows:** Run `mongod` from Command Prompt.
  - **macOS/Linux:** Run `mongod` in your terminal.

> **Tip:** You can use [MongoDB Compass](https://www.mongodb.com/try/download/compass) for a GUI to view your database.

### 4. Install Ollama for LLM

- Download and install Ollama from [https://ollama.com/download](https://ollama.com/download).
- Start the Ollama server and pull a model, e.g.:
  ```sh
  ollama run llama3
  ```
- Make sure the Ollama API is running at `http://localhost:11434`.

### 5. Set up a virtual environment

```sh
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 6. Install dependencies

```sh
pip install -r requirements.txt
```

### 7. Configure environment

Create a `.env` file in the root directory with content like:

```env
FLASK_SECRET_KEY=your_secret_key
MONGO_URI=mongodb://localhost:27017/calendar
OLLAMA_MODEL_NAME=llama3.2
OLLAMA_API_URL=http://localhost:11434/api/generate
```

- Replace `your_secret_key` with a secure random string.

### 8. Run the application

```sh
python run.py
```

Access the app at [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

---

## 🧠 AI Integration

The app communicates with a local Ollama server to process calendar-related natural language requests. You can adapt the AI backend for OpenAI or other APIs by modifying [`app/services/ai_assistant.py`](app/services/ai_assistant.py).

---

## 📂 Contributions

PRs are welcome. Please follow PEP8 and modular design guidelines.

---

## 🛡 License

MIT License. See LICENSE for details.

---

## Useful Links

- [Python Downloads](https://www.python.org/downloads/)
- [MongoDB Community Server](https://www.mongodb.com/try/download/community)
- [MongoDB Compass (GUI)](https://www.mongodb.com/try/download/compass)
- [Ollama LLM](https://ollama.com/download)
- [Flask Documentation](https://flask.palletsprojects.com/)
