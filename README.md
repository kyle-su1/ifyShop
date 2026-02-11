# ifyShop (CxC 2026)

Our AI powered multi-agent platform to suggest shopping items via screenshot, scraped reviews, and user preferences.

**Goal**: Visual product analysis, identification, market research, price comparison, and AI-powered Eco Scores.

---

## 🚀 Quick Start Guide

### Prerequisites
*   **Docker Desktop** (running)
*   **Node.js** (v18+) & `npm` (optional, for local frontend dev)
*   **Python 3.11+** (optional, for local backend dev)

### 1. Clone & Setup
```bash
git clone <repo-url>
cd CxC2026
```

### 2. Configure Environment
Create `.env` files in both `backend/` and `frontend/` directories.

**Backend (`backend/.env`):**
```ini
# Core Keys
GOOGLE_API_KEY=your_gemini_key
TAVILY_API_KEY=tvly-xxx
SERPAPI_API_KEY=your_serpapi_key
IMGBB_API_KEY=your_imgbb_key

# Auth0 (Backend)
AUTH0_DOMAIN=dev-xxx.us.auth0.com
AUTH0_AUDIENCE=https://cxc2026-api
AUTH0_ALGORITHMS=["RS256"]
AUTH0_ISSUER=https://dev-xxx.us.auth0.com/

# Optional: Snowflake (for Cache/Vector Search)
SNOWFLAKE_ACCOUNT=xxx
SNOWFLAKE_USER=xxx
SNOWFLAKE_PASSWORD=xxx
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=CXC_APP
SNOWFLAKE_SCHEMA=PUBLIC
```

**Frontend (`frontend/.env`):**
```ini
# Auth0 (Frontend)
VITE_AUTH0_DOMAIN=dev-xxx.us.auth0.com
VITE_AUTH0_CLIENT_ID=your_client_id
VITE_AUTH0_AUDIENCE=https://cxc2026-api
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Run with Docker
```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f
```

Access apps at:
*   **Frontend**: http://localhost:5173
*   **Backend API**: http://localhost:8000/docs

---

## 🏗️ Architecture

The system uses a **multi-stage agentic pipeline** orchestrated by **LangGraph**.

![alt text](image.png)

👉 **[Read the full Architecture Documentation](docs/architecture.md)** for detailed node responsibilities, scoring logic, and data flow.

---

## 🛠️ Troubleshooting

**1. "Backend Connection Refused"**
*   Ensure `VITE_API_BASE_URL` is correct.
*   Check if backend is running: `docker-compose ps`.
*   Wait for the backend to fully start (health check will spin in frontend).

**2. "Google Lens Failed"**
*   Check `IMGBB_API_KEY`. Images must be public for Lens to see them.
*   Check `SERPAPI_API_KEY`.

**3. "Database Connection Failed"**
*   Ensure PostgreSQL container is healthy (`docker-compose ps`).

---

## Tech Stack

**Backend**
- **FastAPI**: High-performance API framework.
- **LangGraph**: Orchestrates the multi-agent state machine.
- **PostgreSQL**: Primary database for user data.
- **Snowflake**: Data warehouse for product catalog and vector search.
- **Auth0**: Secure authentication.
- **Docker**: Containerization.

**Frontend**
- **React**: UI library.
- **Vite**: Fast build tool (replacing Next.js).
- **Tailwind CSS**: Styling.
- **Auth0 React SDK**: Frontend auth integration.

**AI & APIs**
- **Google Gemini 2.0 Flash**: Core LLM for Vision and Reasoning.
- **Tavily AI**: Optimized search for LLMs (Product & Company Sustainability Data).
- **SerpAPI**: Google Lens and Shopping data.
- **ImgBB**: Image hosting for Lens integration.

