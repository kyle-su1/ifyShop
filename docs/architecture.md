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

### **On-Demand Google Lens Identification**
The Vision Node provides fast initial detection, but for **specific product identification** (e.g., "Keychron K2 HE" instead of "Mechanical Keyboard"), we use **SerpAPI Google Lens** on-demand.

#### **Why On-Demand?**
*   **Latency**: Lens API calls take 5-10 seconds each. Calling for every object during initial analysis would add 30+ seconds.
*   **Cost**: SerpAPI charges per call. On-demand means we only pay for objects the user actually clicks.
*   **User Experience**: Initial bounding boxes appear fast (~2-5s), then specific identification happens when needed.

#### **Architecture**
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

#### **Implementation Files**
| File | Purpose |
|------|---------|
| `backend/app/services/lens_identify.py` | SerpAPI Lens API integration |
| `backend/app/services/image_crop.py` | Crop images to bounding box coordinates |
| `backend/app/services/image_hosting.py` | Temporary image hosting (ngrok fallback) |
| `backend/app/api/endpoints/identify.py` | On-demand `/identify` endpoint |
| `frontend/src/lib/api.js` | `identifyObject()` function |

#### **Image Hosting Strategy**
SerpAPI requires a **publicly accessible URL** for the image. Two options:
1.  **ImgBB (Preferred)**: Fast CDN, direct base64 upload, no tunnel required.
    *   Requires `IMGBB_API_KEY` in `.env`
2.  **Ngrok (Fallback)**: Tunnels local server to public URL.
    *   Requires `PUBLIC_BASE_URL=https://xxx.ngrok-free.app` in `.env`

#### **Lens Response Parsing**
```python
# Priority order for extracting product name:
1. knowledge_graph.title    # Most authoritative (95% confidence)
2. visual_matches[0].title  # Good fallback (80% confidence)
3. shopping_results[0].title # Commercial products (85% confidence)
4. Gemini's original name   # Last resort (50% confidence)
```

#### **Frontend Caching**
Results are cached in React state (`identifiedCache`) by object index:
```javascript
// First click: API call → cache result
// Second click: Instant from cache
const [identifiedCache, setIdentifiedCache] = useState({});
```

#### **Environment Variables**
| Variable | Required | Description |
|----------|----------|-------------|
| `SERPAPI_API_KEY` | Yes | SerpAPI account key |
| `IMGBB_API_KEY` | Recommended | ImgBB API key for fast hosting |
| `PUBLIC_BASE_URL` | Fallback | Ngrok URL if no ImgBB key |



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
*   **Strategy**: Hybrid Discovery (Internal + External Fusion).
*   **Vector Feedback Loop** _[NEW]_:
    *   Validated external findings (from Tavily) are **upserted** to Snowflake `products` with 3072-dim embeddings.
    *   **Purpose**: Continually expands the internal knowledge base with high-quality findings.

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

**Selected Path**: Hybrid (PostgreSQL + Snowflake).

*   **Users & Auth**: PostgreSQL (User profiles, preferences, session data).
*   **Product Catalog & Vectors**: Snowflake (Schema: `CXC_APP.PUBLIC.PRODUCTS`).
    *   **Vector Search**: Uses `VECTOR(FLOAT, 3072)` (Gemini-001) and `VECTOR_COSINE_SIMILARITY`.
    *   **Purpose**: Enabling scalable "Check Internal Database" lookups for the Agent.
    *   **Embedding Model**: `models/gemini-embedding-001`.

---

## 7. Snowflake Caching Strategy

Snowflake is used to **reduce latency** and **minimize API costs** by caching repeated queries in a dedicated cache table. This leverages our existing Snowflake connection.

### **Cache Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                      Request Flow                            │
│                                                              │
│  User Request                                                │
│       │                                                      │
│       ▼                                                      │
│  ┌───────────────┐  cache hit   ┌─────────────┐             │
│  │  QUERY_CACHE  │ ───────────► │  Fast       │             │
│  │    (Table)    │              │  Response   │             │
│  └───────────────┘              └─────────────┘             │
│       │                                                      │
│       │ cache miss                                           │
│       ▼                                                      │
│  ┌─────────────────┐                                        │
│  │  External APIs  │  (Tavily, SerpAPI, Vision)             │
│  └─────────────────┘                                        │
│       │                                                      │
│       │ cache result                                         │
│       ▼                                                      │
│  ┌───────────────┐                                          │
│  │  QUERY_CACHE  │  (with TTL expiry)                       │
│  └───────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

### **Cache Table Schema**
```sql
CREATE TABLE IF NOT EXISTS CXC_APP.PUBLIC.QUERY_CACHE (
    cache_key VARCHAR(64) PRIMARY KEY,    -- MD5 hash of query params
    cache_type VARCHAR(50),               -- 'tavily', 'serpapi', 'skeptic'
    query_params VARIANT,                 -- Original request params (JSON)
    cached_result VARIANT,                -- Response data (JSON)
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    expires_at TIMESTAMP_NTZ,             -- For TTL filtering
    hit_count INT DEFAULT 0               -- Analytics
);
```

### **Cache Keys & TTLs**

| Data Type | Key Pattern | TTL | expires_at Calculation |
|-----------|------------|-----|------------------------|
| **Tavily Search** | `tavily:{hash(query)}` | 1 hour | `DATEADD(hour, 1, CURRENT_TIMESTAMP())` |
| **SerpAPI Prices** | `serpapi:{hash(product_name)}` | 15 minutes | `DATEADD(minute, 15, CURRENT_TIMESTAMP())` |
| **Skeptic Analysis** | `skeptic:{product}:{hash(reviews)}` | 30 minutes | `DATEADD(minute, 30, CURRENT_TIMESTAMP())` |

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
### **Node 6: Chat & Router Loop (The "Conversation")** _[NEW]_
*   **Trigger**: User sends a follow-up message or uploads an image.
*   **Component**: `backend/app/agent/nodes/router.py`
*   **Model**: **Gemini 2.0 Flash** (`gemini-2.0-flash`).
*   **Logic**: Classifies intent into:
    1.  `vision_search`: New image analysis.
    2.  `chat`: General Q&A about the current product.
    3.  `update_preferences`: User states a new constraint (e.g., "I need it under $50").
    4.  `market_scout_search`: User wants specific alternatives (e.g., "Find me a blue one").
*   **Feedback Loop**:
    *   **Vector Feedback**: Validated external findings (from Tavily) are **upserted** to Snowflake `products` with 3072-dim embeddings.
    *   **Preference Learning**: User constraints are saved to the User Profile (Postgres) and influence future `Analysis` node scoring.
