# Finae Project Runbook

This guide provides step-by-step instructions to set up and run the **Finae** application locally on a Windows machine. The project consists of a Python FastAPI backend and a React frontend.

## Prerequisites
Ensure you have the following installed on your system:
- **Python 3.10+**: You can download it from [python.org](https://www.python.org/downloads/).
- **Node.js 18+ & npm**: You can download it from [nodejs.org](https://nodejs.org/).
- **Git**: To clone the repository (if not already cloned).
- A Groq API key: Required for the AI assistant functionality ([Console](https://console.groq.com)).
- A MongoDB Connection String (if applicable for database features).

---

## 1. Backend Setup (FastAPI)

The backend uses Python. We will create a virtual environment to manage dependencies locally without affecting your system Python installation.

### Step 1.1: Open PowerShell and navigate to the backend folder
```powershell
cd g:\dem\Finae\backend
```

### Step 1.2: Create a Virtual Environment
```powershell
python -m venv venv
```
*This creates a folder named `venv` containing the isolated Python environment.*

### Step 1.3: Activate the Virtual Environment
```powershell
.\venv\Scripts\activate
```
*You should now see `(venv)` at the beginning of your PowerShell prompt.*

### Step 1.4: Install Python Requirements
Install all the necessary packages listed in `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### Step 1.5: Configure Environment Variables
You need to set up your `.env` file for API keys.
1. Copy the example file to create your own `.env` file:
```powershell
Copy-Item .env.example .env
```
2. Open the `.env` file in your editor and add your **GROQ_API_KEY** (and any required MongoDB connection strings).

### Step 1.6: Run the Backend Server
Start the FastAPI server using Uvicorn:
```powershell
uvicorn server:app --reload --port 8000
```
*The backend is now running at `http://localhost:8000`.*
*(Leave this PowerShell window open to keep the backend running)*

---

## 2. Frontend Setup (React)

The frontend is built with React and needs Node.js.

### Step 2.1: Open a NEW PowerShell window and navigate to the frontend folder
```powershell
cd g:\dem\Finae\frontend
```

### Step 2.2: Install Node Dependencies
Install all the necessary packages listed in `package.json`:
```powershell
npm install
```

### Step 2.3: Configure Environment Variables
Create a `.env` file to tell the frontend where to find the backend API:
```powershell
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env
```

### Step 2.4: Run the Frontend Development Server
Start the React application:
```powershell
npm start
```

*The frontend should automatically open in your default browser at `http://localhost:3000`.*
*(Leave this PowerShell window open to keep the frontend running)*

---

## Summary of Running the App (Daily Routine)

Whenever you want to start the project again in the future, you just need to do the following:

**Terminal 1 (Backend):**
```powershell
cd g:\dem\Finae\backend
.\venv\Scripts\activate
uvicorn server:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```powershell
cd g:\dem\Finae\frontend
npm start
```
