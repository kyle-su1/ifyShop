# Agent Architecture & Setup Guide

**Project**: Shopping Suggester Agent (CxC 2026)
**Goal**: Visual product analysis, identification, market research, and personalized recommendations.

---

## 🚀 Quick Start Guide

### Prerequisites
*   **Docker Desktop** (running)
*   **Node.js** (v18+) & `npm` (optional, for local frontend dev)
*   **Python 3.11+** (optional, for local backend dev)
*   **ngrok** (optional, for public URL if using local dev)

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
VITE_API_URL=http://localhost:8000
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

## 🏗️ Architecture Overview

The system uses a **Two-Stage Pipeline** managed by **LangGraph**.

### Stage 1: Fast Detection (Instant)
**Goal**: Show bounding boxes immediately.
1.  **Frontend uploads image** to `/api/v1/agent/analyze` (flag: `detect_only=True`).
2.  **Vision Node (Gemini 2.0 Flash)**:
    *   Detects all objects.
    *   Returns bounding boxes.
    *   **STOPS execution**.
3.  **Frontend**: Renders interactive boxes over the image.
    *   *Latency: ~2 seconds.*

### Stage 2: Deep Analysis (On-Demand)
**Goal**: Analyze a specific product selected by the user.
1.  **User clicks a bounding box**.
2.  **Frontend calls `/api/v1/agent/identify`**:
    *   Crops image to box.
    *   Uploads to ImgBB.
    *   Calls **SerpAPI Google Lens**.
    *   Returns precise product name (e.g., "Keychron Q5 Max").
3.  **Frontend resumes analysis** via `/api/v1/agent/analyze` (flag: `skip_vision=True`):
    *   Passes the identified `product_name`.
    *   **Market Scout Node**: Searches for prices, reviews, and competitors (parallelized).
    *   **Critique Node**: Checks for fake reviews.
    *   **Analysis Node**: Scores products based on user preferences.
    *   **Response Node**: Generates final recommendation.

---

## 🧩 Service Breakdown

| Service | Technology | Port | Purpose |
|---------|------------|------|---------|
| **frontend** | React + Vite | 5173 | Interactive UI, Image Upload, Bounding Boxes |
| **backend** | FastAPI | 8000 | Agent API, LangGraph Workflow |
| **db** | PostgreSQL | 5433 | User Profiles, Session History |
| **redis** | Redis | 6379 | API Response Caching (Tavily/SerpAPI) |

### Docker Configuration
*   **Hot Reload**: Both Frontend and Backend are configured for hot-reloading in Docker.
*   **Network**: All services share a `cxc-network`.

---

## 🛠️ Troubleshooting

**1. "Backend Connection Refused"**
*   Ensure `VITE_API_URL` is correct.
*   Check if backend is running: `docker-compose ps`.

**2. "Google Lens Failed"**
*   Check `IMGBB_API_KEY`. Images must be public for Lens to see them.
*   Check `SERPAPI_API_KEY`.

**3. "Database Connection Failed"**
*   Ensure PostgreSQL container is healthy (`docker-compose ps`).
*   Check credentials in `micros/auth/app/core/config.py` (default: `user`/`password`).

---

## 🧠 Core Agents (LangGraph)

1.  **Vision Agent** (Gemini): "The Eye". Detects objects.
2.  **Market Scout** (Tavily + Gemini): "The Explorer". Finds prices & alternatives.
3.  **Skeptic** (Gemini): "The Critic". Detects fake reviews/scams.
4.  **Analyst** (Gemini): "The Brain". Scores products 0-100.
