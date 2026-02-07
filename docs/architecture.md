# Agent Workflow Architecture

This document outlines the architecture for the **Shopping Suggester** agent workflow. The system is designed to take a user's visual input (screenshot) and query, identify the product, research it across the web, and provide personalized recommendations based on user preferences.

## 1. High-Level Architecture

The core of the system is a **Multi-Agent System** orchestrated by **LangGraph**. The entire stack is **containerized with Docker** for consistency and easy deployment.

### Tech Stack Overview
- **Orchestration**: LangGraph
- **LLMs**:
  - **Vision/Parsing**: OpenAI GPT-4o (via OpenRouter), Google Cloud Vision API
  - **Reasoning/Analysis**: Gemini 1.5 Pro / 2.0 Flash
- **Tools**:
  - **Search**: Tavily API (General search, identifying products)
  - **Pricing**: SerpAPI (Google Shopping data)
  - **Scraping**: LangChain Web Scrapers
- **Database**: PostgreSQL (Docker container)
- **Backend & API**: FastAPI (Docker container)
- **Frontend**: React + Vite (Docker container)
- **Authentication**: Auth0

---

## 2. Docker Architecture

All services run in Docker containers managed by `docker-compose.yml`:

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
├─────────────────┬─────────────────┬─────────────────────┤
│   frontend      │    backend      │        db           │
│   (React/Vite)  │   (FastAPI)     │   (PostgreSQL)      │
│   Port: 5173    │   Port: 8000    │   Port: 5433        │
└─────────────────┴─────────────────┴─────────────────────┘
```

### Services

| Service | Image/Build | Port | Description |
|---------|-------------|------|-------------|
| **db** | `postgres:13-alpine` | 5433:5432 | PostgreSQL database with healthcheck |
| **backend** | `./backend` | 8000:8000 | FastAPI with uvicorn, hot-reload |
| **frontend** | `./frontend` | 5173:5173 | Vite dev server |

### Running the Stack

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Environment Variables

| File | Purpose |
|------|---------|
| `backend/.env` | Backend secrets (API keys, database URL) |
| `frontend/.env` | Frontend config (Auth0 domain, client ID) |

**Note**: `DATABASE_URL` is overridden in docker-compose to use container networking (`db:5432` instead of `localhost:5433`).

---

## 3. Agent Workflow (LangGraph)

The workflow is a Directed Acyclic Graph (DAG) managed by LangGraph.

### **Node 1: User Intent & Vision (The "Eye")**
*   **Input**: User uploaded image (Screenshot) + Text Prompt.
*   **Tools**: OpenAI GPT-4o (via OpenRouter), Google Cloud Vision.
*   **Responsibilities**:
    1.  **Object Detection**: Identify the primary item in the screenshot.
    2.  **Interactive Selection Data**: Return bounding boxes for identified items.
    3.  **Context Extraction**: Read text on screen (OCR).
*   **Output**: Structured Product Query.

### **Node 2: Discovery Layer (The "Researcher" & "Explorer")**
This phase runs two parallel agents to gather deep data.

### **Node 2a: Product Researcher (The "Deep Dive")**
*   **Input**: Structured Product Query (from Node 1).
*   **Goal**: Gather comprehensive data on the *specific* product identified.
*   **Agents**:
    *   **Search Agent**: Uses **Tavily API** to find listings.
    *   **Price Checker**: Uses **SerpAPI** for pricing.

### **Node 2b: Market Scout (The "Explorer")**
*   **Input**: Structured Product Query + User Preferences.
*   **Goal**: Find relevant *alternatives* based on the user's needs.

### **Node 3: The Skeptic (Critique & Verification)**
*   **Input**: Raw product data + Alternative Candidates.
*   **Agent**: **Skeptic Agent** (`gemini-2.0-flash`).
*   **Responsibilities**:
    1.  **Fake Review Detection**: Analyze patterns in reviews.
    2.  **Deal Verification**: Check if the "sale price" is legitimate.
*   **Output**: `ReviewSentiment` object with trust score, sentiment, red flags.
*   **Implementation**: [`backend/app/agent/skeptic.py`](file:///Users/kylesu/Desktop/CxC2026/backend/app/agent/skeptic.py)

### **Node 4: Analysis & Synthesis (The "Brain")**
*   **Input**: Product Data + Scout Data + Risk Report.
*   **Agent**: **Analyst Agent** (Gemini 1.5 Pro).
*   **Input**: Product Data + Contextual Scout Data + Risk Report + User Preferences.
*   **Logic**:
    1.  **Preference Loading**: Retrieves explicit user weights (Price, Quality, etc.) and learned preferences from past interactions.
    2.  **Skeptic Analysis Loop**: Invokes the **Skeptic Agent (Node 3 logic)** for *every* candidate (Main Product + Alternatives). This ensures all products have a comparable **Trust Score** and **Sentiment Score** based on review analysis.
    3.  **Weighted Scoring**: Calculates a final match score (0-100) for each product based on:
        *   **Price Score**: Normalized against the market average.
        *   **Quality Score**: Derived from Sentiment + Trust.
        *   **Personalization**: Applied user weights.
    4.  **Ranking**: Sorts all products to determine the best recommendation (Original Selection vs. Alternatives).
*   **Output**: Structured Analysis Object with `recommended_product` and `alternatives_ranked`.

### **Node 5: Response Formulation (The "Speaker")**
*   **Input**: Structured Analysis Object.
*   **Output**: Final JSON Payload with Verdict, Pros/Cons, Pricing.

### **Node 6: Chat/Refinement Loop**
*   **Trigger**: User sends follow-up messages.
*   **Action**: Loop back to research or analysis nodes as needed.

---

## 4. Backend Routes

### **Authentication (Auth0 Integration)**
*   `GET /api/v1/users/me`: Returns current user profile.
*   `PATCH /api/v1/users/preferences`: Update user preferences.

### **Core Workflow**
*   `POST /api/v1/agent/analyze-image`:
    *   **Input**: `{ "imageBase64": "data:image/..." }`
    *   **Output**: Detected objects with bounding boxes.
*   `POST /api/v1/agent/recommend`:
    *   **Input**: User preferences + Current item context.
    *   **Output**: Full recommendation JSON.

### **History & Storage**
*   `GET /api/v1/history`: List past queries.
*   `GET /api/v1/history/{id}`: Specific details.

---

## 5. Database Strategy

**Selected Path**: PostgreSQL (containerized) for all data.

*   **Users & Auth**: User profiles, preferences, session data
*   **Search History**: Past queries and recommendations
*   **Future**: Can add pgvector for vector search if needed

---

## 6. Deployment Strategy

### Local Development
```bash
docker-compose up -d
```

### Production
*   **Containerization**: All services are Dockerized
*   **Infrastructure**: AWS ECS (Fargate) or similar
*   **Auth**: Auth0 handles JWT; Backend verifies tokens
