# Agent Workflow Architecture

This document outlines the architecture for the **Shopping Suggester** agent workflow. The system is designed to take a user's visual input (screenshot) and query, identify the product, research it across the web, and provide personalized recommendations based on user preferences.

## 1. High-Level Architecture

The core of the system is a **Multi-Agent System** orchestrated by **LangGraph**. The entire stack is **containerized with Docker** for consistency and easy deployment.

### Tech Stack Overview
- **Orchestration**: LangGraph
- **LLMs**:
  - **Vision/Parsing**: **Gemini 2.0 Flash** - Primary model for object detection and OCR.
  - **Reasoning/Analysis**: **Gemini 2.0 Flash** - Used for Market Scout, Skeptic, and detailed Analysis.
  - **Response Formatting**: **Gemini 2.0 Flash** - Fast response generation and formatting.
- **Caching**:
  - **Redis**: In-memory cache for API responses (Tavily, SerpAPI) with configurable TTL
  - **Purpose**: Reduce redundant API calls, lower latency, save costs
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
┌───────────────────────────────────────────────────────────────────┐
│                       Docker Compose                               │
├─────────────┬─────────────┬─────────────────┬─────────────────────┤
│  frontend   │   backend   │       db        │       redis         │
│ (React/Vite)│  (FastAPI)  │  (PostgreSQL)   │    (Cache Layer)    │
│  Port: 5173 │  Port: 8000 │   Port: 5433    │    Port: 6379       │
└─────────────┴─────────────┴─────────────────┴─────────────────────┘
```

### Services

| Service | Image/Build | Port | Description |
|---------|-------------|------|-------------|
| **db** | `postgres:13-alpine` | 5433:5432 | PostgreSQL database with healthcheck |
| **backend** | `./backend` | 8000:8000 | FastAPI with uvicorn, hot-reload enabled via command override |
| **frontend** | `./frontend` | 5173:5173 | Vite dev server, hot-reload enabled |
| **redis** | `redis:7-alpine` | 6379:6379 | In-memory cache for API responses |

### Running the Stack

```bash
# Start all services (rebuilds if necessary)
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Environment Variables & Setup Fixes

To ensure the stack runs correctly (based on recent fixes):

1.  **Backend Configuration**:
    *   Create `backend/.env`.
    *   Required Keys: `GOOGLE_API_KEY`, `TAVILY_API_KEY`, `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`.
    *   **Fix**: `requirements.txt` must include `google-generativeai`, `langgraph`, `langchain`, `google-search-results`.

2.  **Frontend Configuration**:
    *   Create `frontend/.env`.
    *   Required Keys: `VITE_AUTH0_DOMAIN`, `VITE_AUTH0_CLIENT_ID`, `VITE_AUTH0_AUDIENCE`, `VITE_API_URL`.

3.  **Build Optimizations**:
    *   **Frontend**: A `.dockerignore` file was added to exclude `node_modules` and `dist`. This prevents massive build contexts and significantly speeds up `docker-compose build frontend`.
    *   **Commands**: `docker-compose.yml` overrides default commands to ensure explicit host binding (`0.0.0.0`) for both FastAPI and Vite, fixing access issues from the host machine.

---

## 3. Agent Workflow (LangGraph)

The workflow is a Directed Acyclic Graph (DAG) managed by LangGraph.

### **Node 1: User Intent & Vision (The "Eye")**
*   **Input**: User uploaded image (Screenshot) + Text Prompt.
*   **Model**: **Gemini 2.0 Flash**.
*   **Responsibilities**:
    1.  **Multi-Object Detection**: Identifies **all** distinct objects/products in the image.
    2.  **Bounding Boxes**: Returns normalized coordinates [ymin, xmin, ymax, xmax] for each object.
    3.  **Context Extraction**: Reads text on screen (OCR).
*   **Output**: Structured Product Query containing a list of `detected_objects`.

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
    *   **Tavily Search**: For live web results.
    *   **Snowflake Vector Search**: For internal product catalog similarity (Cosine Similarity).
*   **Model**: **Gemini 2.0 Flash** (`gemini-2.0-flash`) for fast candidate extraction.

### **Node 3: The Skeptic (Critique & Verification)**
*   **Input**: Raw product data (Main Item) + Alternative Candidates (Scout).
*   **Agent**: **Skeptic Agent** (`gemini-2.0-flash`).
    > **Model Selection**: Uses `gemini-2.0-flash` (via `MODEL_REASONING`) for fast, cost-effective reasoning.
    > **Note**: Originally planned for Snowflake Cortex, but migrated to Gemini for lower latency.
*   **Caching**: Review analysis results are cached in Redis keyed by `product_name + review_hash` (TTL: 30 minutes).
*   **Responsibilities**:
    1.  **Fake Review Detection**: Analyze patterns in reviews for the main product.
    2.  **Deal Verification**: Check if the "sale price" is actually a tactic.
    3.  **Cross-Exam**: Check if the "Alternates" suggested by the Scout hold up to scrutiny.
*   **Output**: `ReviewSentiment` object containing:
    - `trust_score` (0-10): Credibility of the reviews.
    - `sentiment_score` (-1 to 1): Weighted sentiment.
    - `red_flags`: List of suspicious patterns detected.
    - `summary`, `pros`, `cons`, `verdict`: Human-readable analysis.
*   **Implementation**: [`backend/app/agent/nodes/critique.py`](backend/app/agent/nodes/critique.py)

### **Node 4: Analysis & Synthesis (The "Brain")**
*   **Input**: Product Data + Contextual Scout Data + Risk Report.
*   **Agent**: **Analyst Agent** (Gemini 2.0 Flash).
*   **Logic**:
    1.  **Preference Loading**: Retrieves explicit user weights.
    2.  **Weighted Scoring**: Calculates a final match score (0-100) for each product based on price, quality, and trust.
    3.  **Ranking**: Sorts all products to determine the best recommendation.
*   **Output**: Structured Analysis Object.

### **Node 5: Response Formulation (The "Speaker")**
*   **Input**: Structured Analysis Object.
*   **Model**: **Gemini 2.0 Flash** (`gemini-2.0-flash`).
    > **Model Selection**: Uses `gemini-2.0-flash` for fast response generation and formatting.
*   **Responsibilities**:
    1.  **Final Recommendation**: Generate an empathetic, human-like summary.
    2.  **Format Output**: JSON for frontend (Verdict, Pros/Cons, Pricing).
*   **Output**: JSON Payload.

---

## 4. Frontend Integration

### **Interactive Bounding Boxes**
The frontend (`DashboardPage.jsx`) uses the `detected_objects` list from the API response to render interactive overlays:

1.  **Rendering**: A `BoundingBoxOverlay` component is mapped over the `detected_objects` array.
2.  **Coordinates**: Gemini returns normalized coordinates (0-1000). The frontend converts these to percentage-based CSS (`top`, `left`, `width`, `height`) to overlay correctly on the responsive image.
3.  **Interaction**: Hovering over a box displays the object's name and confidence score.
4.  **Layout**: The image container uses `flex-shrink-0` to ensure it remains visible and sized correctly even when the detailed analysis results (alternatives list) expand below it.

### Recommendation Output (JSON)
The final payload sent to the frontend includes the active product data for visualization:

```json
{
  "active_product": {
    "name": "Robotic Dog",
    "bounding_box": [200, 300, 600, 700],
    "detected_objects": [
        { "name": "Robotic Dog", "bounding_box": [...], "confidence": 0.95 },
        { "name": "Remote Control", "bounding_box": [...], "confidence": 0.88 }
    ]
  },
  "outcome": "highly_recommended",
  "identified_product": "Herman Miller Aeron Chair",
  "price_analysis": { ... },
  "community_sentiment": { ... },
  "alternatives": [ ... ]
}
```

---

## 5. Backend Routes

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

### **Session Management (Multi-Chat)**
*   `POST /api/v1/sessions`: Create a new analysis session → Returns `{ "session_id": "uuid" }`.
*   `GET /api/v1/sessions`: List all active sessions for the current user.
*   `GET /api/v1/sessions/{id}`: Get full session state (product, analysis, chat history).
*   `POST /api/v1/sessions/{id}/analyze`: Upload image and trigger analysis pipeline for this session.
*   `POST /api/v1/sessions/{id}/chat`: Send a chat message within the session.
*   `DELETE /api/v1/sessions/{id}`: Close session (saves to history, clears from active).
*   `WebSocket /api/v1/sessions/{id}/stream`: Real-time streaming of analysis progress.

### **History & Storage**
*   `GET /api/v1/history`: List past queries.
*   `GET /api/v1/history/{id}`: Specific details.

---

## 6. Database Strategy

**Selected Path**: PostgreSQL (containerized) for all data.

*   **Users & Auth**: User profiles, preferences, session data
*   **Search History**: Past queries and recommendations
*   **Sessions**: Active chat sessions with state checkpoints
*   **Future**: Can add pgvector for vector search if needed

---

## 7. Redis Caching Strategy

Redis is used to **dramatically reduce latency** and **minimize API costs** by caching repeated queries. This is critical for the "wow factor" of speed.

### **Cache Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                      Request Flow                            │
│                                                              │
│  User Request                                                │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────┐    cache hit     ┌─────────────┐               │
│  │  Redis  │ ───────────────► │  Instant    │               │
│  │  Cache  │                  │  Response   │               │
│  └─────────┘                  └─────────────┘               │
│       │                                                      │
│       │ cache miss                                           │
│       ▼                                                      │
│  ┌─────────────────┐                                        │
│  │  External APIs  │  (Tavily, SerpAPI, Vision)             │
│  └─────────────────┘                                        │
│       │                                                      │
│       │ cache result                                         │
│       ▼                                                      │
│  ┌─────────┐                                                │
│  │  Redis  │                                                │
│  └─────────┘                                                │
└─────────────────────────────────────────────────────────────┘
```

### **Cache Keys & TTLs**

| Data Type | Key Pattern | TTL | Rationale |
|-----------|------------|-----|-----------|
| **Tavily Search** | `tavily:{hash(query)}` | 1 hour | Search results change slowly |
| **SerpAPI Prices** | `serpapi:{hash(product_name)}` | 15 minutes | Prices fluctuate more often |
| **Vision Detection** | `vision:{hash(image_base64[:100])}` | 24 hours | Same image = same objects |
| **Skeptic Analysis** | `skeptic:{product_name}:{hash(reviews)}` | 30 minutes | Reviews don't change within session |
| **LLM Responses** | `llm:{model}:{hash(prompt)}` | 10 minutes | For identical prompts only |

### **Implementation Example (Python)**
```python
import redis
import hashlib
import json
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cached(prefix: str, ttl_seconds: int):
    """Decorator for caching function results in Redis."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function args
            key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
            cache_key = f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"
            
            # Check cache
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            redis_client.setex(cache_key, ttl_seconds, json.dumps(result))
            return result
        return wrapper
    return decorator

# Usage
@cached(prefix="tavily", ttl_seconds=3600)
async def search_tavily(query: str) -> dict:
    # ... actual API call
    pass
```

### **Cache Invalidation**
*   **Automatic TTL expiry**: Most cache entries auto-expire.
*   **Manual invalidation**: Admin endpoint `POST /api/v1/admin/cache/clear` for emergencies.
*   **Version-based keys**: If APIs change, bump the version in key prefix (e.g., `tavily:v2:{hash}`).

### **Expected Performance Gains**

| Scenario | Without Cache | With Cache | Improvement |
|----------|--------------|------------|-------------|
| Repeat product query (same session) | 3-5 seconds | <100ms | **50x faster** |
| Same product across users | 3-5 seconds | <100ms | **50x faster** |
| Review re-analysis | 2-3 seconds | <50ms | **40x faster** |
| Full pipeline (cold) | 8-12 seconds | 8-12 seconds | No change |
| Full pipeline (warm cache) | 8-12 seconds | 1-2 seconds | **6x faster** |

---

## 8. Deployment Strategy

### Local Development
```bash
docker-compose up -d
```

### Production
*   **Containerization**: All services are Dockerized (FastAPI, React, Postgres, Redis)
*   **Infrastructure**: AWS ECS (Fargate) or similar
*   **Redis Deployment**:
    *   **Development**: Local Redis via Docker
    *   **Production**: AWS ElastiCache (Redis) for managed, scalable caching
*   **Auth**: Auth0 handles JWT; Backend verifies tokens
*   **Secrets Management**: AWS Secrets Manager for API keys

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
| **Node 6: Chat** | `gemini-2.0-flash` | Context-aware conversation with reasoning |
