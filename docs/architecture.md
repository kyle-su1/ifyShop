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
2.  **On-Demand Identification** (`/api/v1/agent/identify`):
    *   Crops image to box.
    *   Uploads to ImgBB.
    *   Calls **SerpAPI Google Lens**.
    *   Returns precise product name (e.g., "Keychron Q5 Max").
3.  **Resume Analysis** (`/api/v1/agent/analyze` - `skip_vision=True`):
    *   Passes the identified `product_name`.
    *   **Market Scout Node**: Searches for prices, reviews, and competitors (parallelized).
    *   **Critique Node**: Checks for fake reviews.
    *   **Analysis Node**: Scores products based on user preferences.
    *   **Response Node**: Generates final recommendation.

#### **On-Demand Flow Diagram**
```
┌──────────────────────────────────────────────────────────────────┐
│                   On-Demand Lens Flow                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   1. Initial Analysis (Fast - Gemini Only)                       │
│      Image → Gemini → Bounding Boxes + Generic Names             │
│      Time: ~2-5 seconds                                          │
│                                                                   │
│   2. User Clicks Bounding Box                                    │
│      Frontend calls: POST /api/v1/agent/identify                 │
│                                                                   │
│   3. On-Demand Identification                                    │
│      ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     │
│      │ Crop Image  │ ──► │ Upload to   │ ──► │ SerpAPI     │     │
│      │ to BBox     │     │ ImgBB/ngrok │     │ Google Lens │     │
│      └─────────────┘     └─────────────┘     └─────────────┘     │
│                                                      │            │
│   4. Result Cached in Frontend State                 ▼            │
│      Subsequent clicks → Instant response      {product_name}    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Deep Dive: Agent Nodes

### **Node 2: Discovery Layer (The "Researcher" & "Explorer")**
This phase runs two parallel agents to gather deep data.

### **Node 2a: Product Researcher (The "Deep Dive")**
*   **Input**: Structured Product Query (from Node 1).
*   **Goal**: Gather comprehensive data on the *specific* product identified.
*   **Agents**:
    *   **Search Agent**: Uses **Tavily API** to find listings.
    *   **Price Checker**: Uses **SerpAPI** for pricing.
*   **Caching**: Results cached in Redis (Tavily: 1 hour TTL, SerpAPI: 15 min TTL).

### **Node 2b: Market Scout (The "Explorer")**
*   **Input**: Structured Product Query + User Preferences.
*   **Goal**: Find relevant *alternatives* based on the user's needs.
*   **Tools**:
    *   **Tavily Search**: For live web results (External Discovery).
    *   **Snowflake Vector Search**: For internal product catalog similarity (Internal Discovery).
*   **Model**: **Gemini 2.0 Flash** (`gemini-2.0-flash`) for fast candidate extraction.
*   **Vector Feedback Loop**:
    *   Validated external findings (from Tavily) are **upserted** to Snowflake `products` with 3072-dim embeddings.
    *   **Purpose**: Continually expands the internal knowledge base with high-quality findings.

### **Node 3: The Skeptic (Critique & Verification)**
*   **Input**: Raw product data (Main Item) + Alternative Candidates (Scout).
*   **Agent**: **Skeptic Agent** (`gemini-2.0-flash`).
*   **Responsibilities**:
    1.  **Fake Review Detection**: Analyze patterns in reviews for the main product.
    2.  **Deal Verification**: Check if the "sale price" is actually a tactic.
    3.  **Cross-Exam**: Check if the "Alternates" suggested by the Scout hold up to scrutiny.

### **Node 4: Analysis & Synthesis (The "Brain")**
*   **Input**: Product Data + Contextual Scout Data + Risk Report.
*   **Agent**: **Analyst Agent** (Gemini 2.0 Flash).
*   **Logic**:
    1.  **Preference Loading**: Retrieves explicit user weights.
    2.  **Weighted Scoring**: Calculates a final match score (0-100) for each product based on price, quality, and trust.
    3.  **Ranking**: Sorts all products to determine the best recommendation.

### **Node 5: Response Formulation (The "Speaker")**
*   **Input**: Structured Analysis Object.
*   **Model**: **Gemini 2.0 Flash** (`gemini-2.0-flash`).
*   **Responsibilities**:
    1.  **Final Recommendation**: Generate an empathetic, human-like summary.
    2.  **Format Output**: JSON for frontend (Verdict, Pros/Cons, Pricing).

### **Node 6: Chat & Router Loop (The "Conversation")**
*   **Trigger**: User sends a follow-up message or uploads an image.
*   **Component**: `backend/app/agent/nodes/router.py`
*   **Model**: **Gemini 2.0 Flash**.
*   **Logic**: Classifies intent into `vision_search`, `chat`, `update_preferences`, or `market_scout_search`.
*   **Feedback Loop**: User constraints influence future scoring.

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

## 9. Model Summary

| Node | Model | Reasoning |
|------|-------|-----------|
| **Node 1: Vision** | `gemini-2.0-flash` | Exclusive model for object detection, bounding boxes, and OCR. |
| **Node 2: Research** | N/A (API calls) | Tavily + SerpAPI, no LLM |
| **Node 2b: Market Scout** | `gemini-2.0-flash` | Fast candidate extraction from search results |
| **Node 3: Skeptic** | `gemini-2.0-flash` | Deep reasoning for fake review detection |
| **Node 4: Analysis** | `gemini-2.0-flash` | Complex multi-factor scoring and ranking |
| **Node 5: Response** | `gemini-2.0-flash` | Fast formatting and data aggregation |
