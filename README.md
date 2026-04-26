# Fin.ae

An AI-powered financial product comparison and lead generation platform built for the UAE market. Users can discover, compare, and apply for insurance, loans, credit cards, bank accounts, and investment products from multiple UAE financial institutions — all in one place.

---

## Features

- **AI Financial Assistant** — Conversational chat powered by Groq (Llama 3.3 70B) that profiles users, answers financial questions, and recommends suitable products
- **Dynamic Product Catalog Injection** — The AI dynamically fetches and incorporates real MongoDB dummy policies into its context window, eliminating hallucinations when answering specific queries
- **Product Recommendations** — Personalised product suggestions filtered by salary, age, residency status, risk appetite, and Sharia compliance
- **Side-by-Side Comparison** — Compare multiple financial products across key attributes in a structured table
- **Application Tracker** — Submit callback requests and track application status per session
- **Financial News** — UAE-focused financial news and market insights
- **Open Chat** — General-purpose financial Q&A outside the product flow

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Tailwind CSS, Framer Motion |
| Backend | FastAPI (Python), Uvicorn |
| AI Model | Groq API — Llama 3.3 70B Versatile |
| Deployment | Vercel (serverless) |
| HTTP Client | Axios (frontend), HTTPX (backend) |

---

## Project Structure

```
Fin.ae/
├── backend/
│   ├── server.py           # FastAPI app — all routes, data models, AI logic
│   ├── requirements.txt    # Python dependencies
│   └── tests/              # Backend tests
├── frontend/
│   ├── src/
│   │   ├── App.js          # Root component, session management, page layout
│   │   ├── api.js          # Axios API client (all backend calls)
│   │   └── components/
│   │       ├── Header.js           # Navigation bar
│   │       ├── Hero.js             # Landing section with CTA
│   │       ├── AvatarChat.js       # AI avatar chat modal (profiling + recommendations)
│   │       ├── Recommendations.js  # Product grid with category filters
│   │       ├── PolicyComparison.js # Side-by-side product comparison table
│   │       ├── ApplicationTracker.js # Application status tracker
│   │       ├── NewsSection.js      # Financial news grid
│   │       ├── OpenChat.js         # General AI chat
│   │       └── Footer.js
│   ├── package.json
│   └── tailwind.config.js
├── api/
│   └── index.py            # Vercel serverless entry point for the backend
├── vercel.json             # Vercel routing config
├── run_backend.sh          # Start FastAPI dev server
├── run_frontend.sh         # Start React dev server
└── runbook.sh              # Full setup and run automation
```

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/chat/message` | Send message to AI assistant |
| POST | `/api/chat/extract-profile` | Extract user financial profile from chat |
| POST | `/api/chat/open` | Open-ended financial Q&A |
| POST | `/api/chat/agent-action` | Execute agent actions (e.g. apply for product) |
| GET | `/api/policies` | List all products (supports category/filter params) |
| GET | `/api/policies/{id}` | Get a single product's details |
| POST | `/api/policies/recommend` | Get AI-personalised recommendations |
| POST | `/api/policies/compare` | Compare selected products |
| POST | `/api/applications` | Submit a callback/application request |
| GET | `/api/applications/{session_id}` | Get applications for a session |
| PATCH | `/api/applications/{id}` | Update application status |
| GET | `/api/news` | Get UAE financial news |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [Groq API key](https://console.groq.com)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # Add your GROQ_API_KEY
uvicorn server:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env
npm start
```

The app will be available at `http://localhost:3000`.

---

## Deployment

The project is configured for Vercel. The `vercel.json` routes all `/api/*` requests to the FastAPI serverless function in `api/index.py` and serves the React build for everything else.

```bash
vercel deploy
```

---

## Design System

- **Primary colour:** Dark green `#0A3224`
- **Accent:** Gold `#D4AF37`
- **Headings:** Cabinet Grotesk
- **Body:** Manrope
- **Style:** Glassmorphism headers, flat cards, bento grid layouts, Framer Motion animations
