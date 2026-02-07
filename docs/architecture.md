# Agent Workflow Architecture

This document outlines the architecture for the **Shopping Suggester** agent workflow. The system is designed to take a user's visual input (screenshot) and query, identify the product, research it across the web, and provide personalized recommendations based on user preferences.

## 1. High-Level Architecture

The core of the system is a **Multi-Agent System** orchestrated by **LangGraph**. The entire stack is **containerized with Docker** for consistency and easy deployment.

### Tech Stack Overview
- **Orchestration**: LangGraph
- **LLMs**:
  - **Vision/Parsing**: OpenAI GPT-4o (via OpenRouter) - primary, Google Cloud Vision API (fallback)
  - **Reasoning/Analysis**: Gemini 1.5 Pro (Skeptic, Analysis, Chat - requires deep reasoning)
  - **Response Formatting**: Gemini 1.5 Flash (Node 5 - fast response generation)
  - **Candidate Extraction**: Gemini 2.0 Flash (Market Scout - quick parsing)
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
| **backend** | `./backend` | 8000:8000 | FastAPI with uvicorn, hot-reload |
| **frontend** | `./frontend` | 5173:5173 | Vite dev server |
| **redis** | `redis:7-alpine` | 6379:6379 | In-memory cache for API responses |

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
| `backend/.env` | Backend secrets (API keys, database URL, Redis URL) |
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
*   **Caching**: Results cached in Redis (Tavily: 1 hour TTL, SerpAPI: 15 min TTL).

### **Node 2b: Market Scout (The "Explorer")**
*   **Input**: Structured Product Query + User Preferences.
*   **Goal**: Find relevant *alternatives* based on the user's needs.
*   **Model**: **Gemini 2.0 Flash** (`gemini-2.0-flash`) for fast candidate extraction.

### **Node 3: The Skeptic (Critique & Verification)**
*   **Input**: Raw product data (Main Item) + Alternative Candidates (Scout).
*   **Agent**: **Skeptic Agent** (`gemini-1.5-pro`).
    > **Model Selection**: Uses `gemini-1.5-pro` for its superior reasoning capabilities in detecting fake reviews, analyzing sentiment nuance, and identifying subtle manipulation patterns.
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
*   **Implementation**: [`backend/app/agent/skeptic.py`](backend/app/agent/skeptic.py)

### **Node 4: Analysis & Synthesis (The "Brain")**
*   **Input**: Product Data + Contextual Scout Data + Risk Report.
*   **Agent**: **Analyst Agent** (`gemini-1.5-pro`).
    > **Model Selection**: Requires `gemini-1.5-pro` for complex multi-factor reasoning: weighing user preferences, normalizing prices, synthesizing trust scores, and making nuanced trade-off decisions.
*   **Logic**:
    1.  **Preference Loading**: Retrieves explicit user weights (Price, Quality, etc.) and learned preferences from past interactions.
    2.  **Skeptic Analysis Loop**: Invokes the **Skeptic Agent (Node 3 logic)** for *every* candidate (Main Product + Alternatives).
    3.  **Weighted Scoring**: Calculates a final match score (0-100) for each product based on:
        *   **Price Score**: Normalized against the market average.
        *   **Quality Score**: Derived from Sentiment + Trust.
        *   **Personalization**: Applied user weights.
    4.  **Ranking**: Sorts all products to determine the best recommendation.
*   **Output**: Structured Analysis Object with `recommended_product` and `alternatives_ranked`.

### **Node 5: Response Formulation (The "Speaker")**
*   **Input**: Data from Node 3 (`risk_report`) + Node 4 (`analysis_object`, `alternatives_analysis`).
*   **Model**: **Gemini 2.0 Flash** (`gemini-2.0-flash`) via `MODEL_RESPONSE` config.
    > **Model Selection**: Uses the fast `gemini-2.0-flash` because this node focuses on **formatting** and **summarization** rather than complex reasoning.
*   **Responsibilities**:
    1.  **Main Product Analysis**: Detailed breakdown of the product user is viewing (summary, pros, cons, price analysis, community sentiment).
    2.  **Alternative Suggestions**: For each alternative, provide a summary, pros/cons, and `why_consider` so users can decide for themselves.
    3.  **Final Verdict**: Overall recommendation, but users can still choose based on individual product summaries.
*   **Output**: JSON Payload with structure:
    ```json
    {
      "main_product": {
        "name": "Sony WH-1000XM5",
        "compatibility_score": 85.5,
        "summary": "Detailed analysis...",
        "pros": ["Pro 1", "Pro 2"],
        "cons": ["Con 1"],
        "price_analysis": { "verdict": "Good value", "warnings": [] },
        "community_sentiment": { "trust_level": "High", "summary": "...", "red_flags": [] }
      },
      "alternatives": [
        {
          "name": "Bose QuietComfort Ultra",
          "compatibility_score": 78.2,
          "summary": "Short description for user to decide...",
          "pros": ["Key strength"],
          "cons": ["Key weakness"],
          "why_consider": "Better for users who prioritize comfort"
        }
      ],
      "verdict": "Final recommendation text"
    }
    ```
*   **Implementation**: [`backend/app/agent/nodes/response.py`](backend/app/agent/nodes/response.py)

### **Node 6: Chat/Refinement Loop (The "Conversation")**
*   **Trigger**: User sends a follow-up message (e.g., "What about the warranty?", "Find a cheaper one").
*   **Model**: **Gemini 1.5 Pro** (`gemini-1.5-pro`).
    > **Model Selection**: Chat requires understanding context, recalling previous analysis, and reasoning about new user intents.
*   **Input**: Chat History + Previous Context + Session State.
*   **Action**: Loop back to **Node 2 (Research)** or **Node 4 (Analysis)** depending on if new data is needed.

---

## 3.5 Multi-Session Chat Architecture (Parallel Analysis)

Users can open **multiple chat windows** to analyze different products simultaneously. Each window operates as an independent "session" with its own state.

### **Session Design**
```
┌─────────────────────────────────────────────────────────────┐
│  Frontend: Multi-Tab Interface                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Session A  │  │  Session B  │  │  Session C  │   [+]    │
│  │  Headphones │  │  Laptop     │  │  Chair      │  New     │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend: Session Manager                                    │
│                                                              │
│  session_store = {                                           │
│    "sess_abc123": {                                          │
│      "user_id": "user_1",                                    │
│      "created_at": "2026-02-07T10:00:00Z",                  │
│      "product_query": { ... },                               │
│      "research_data": { ... },                               │
│      "analysis_object": { ... },                             │
│      "chat_history": [                                       │
│        {"role": "user", "content": "Is this a good deal?"},  │
│        {"role": "assistant", "content": "Based on..."}       │
│      ],                                                      │
│      "state_checkpoint": <LangGraph checkpoint>              │
│    },                                                        │
│    "sess_def456": { ... },  // Another parallel session      │
│    "sess_ghi789": { ... }   // Yet another                   │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

### **Session Lifecycle**
1.  **Create Session**: `POST /api/v1/sessions` → Returns `session_id`
2.  **Upload & Analyze**: `POST /api/v1/sessions/{id}/analyze` (triggers full pipeline)
3.  **Chat**: `POST /api/v1/sessions/{id}/chat` (sends message, updates state)
4.  **Get State**: `GET /api/v1/sessions/{id}` (returns current analysis + history)
5.  **Close Session**: `DELETE /api/v1/sessions/{id}` (cleans up, optionally saves to history)

### **Concurrency Model**
*   Each session runs its own **LangGraph instance** with isolated state.
*   Sessions share the **Redis cache** (so if Session A queries "Sony WH-1000XM5", Session B benefits from cached results).
*   **ThreadPoolExecutor** or **asyncio** handles parallel session processing.
*   WebSocket connections allow **real-time streaming** of analysis progress per session.

### **Database Schema: Sessions (Postgres)**
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP DEFAULT NOW(),
    product_name VARCHAR(255),
    state_json JSONB,  -- Full LangGraph state checkpoint
    chat_history JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE
);

-- Index for fast user session lookup
CREATE INDEX idx_sessions_user_active ON sessions(user_id, is_active);
```

---

## 4. Data Flow & Schema

### User Preference Profile (Postgres)
We store weighted vectors for user priorities to customize the **Analysis Node**.
```json
{
  "user_id": "12345",
  "weights": {
    "price_sensitivity": 0.8,
    "durability": 0.9,
    "brand_reputation": 0.5,
    "environmental_impact": 0.3
  }
}
```

### Recommendation Output (JSON)
The final payload sent to the frontend.
```json
{
  "outcome": "highly_recommended",
  "identified_product": "Herman Miller Aeron Chair",
  "price_analysis": {
    "current": 600,
    "market_average": 1200,
    "verdict": "Great Deal (Used/Refurbished price range)"
  },
  "community_sentiment": {
    "summary": "Universally acclaimed for ergonomics.",
    "warnings": ["Mesh can damage clothing", "Size B fits most but check chart"]
  },
  "alternatives": [
    {"name": "Steelcase Leap V2", "match_score": 0.95}
  ]
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
| **Node 1: Vision** | `gpt-4o` (via OpenRouter) | Best-in-class vision with accurate bounding boxes |
| **Node 2: Research** | N/A (API calls) | Tavily + SerpAPI, no LLM |
| **Node 2b: Market Scout** | `gemini-2.0-flash` | Fast candidate extraction from search results |
| **Node 3: Skeptic** | `gemini-2.0-flash` | Fake review detection and price verification |
| **Node 4: Analysis** | `gemini-2.0-flash` | Multi-factor scoring and ranking (`MODEL_ANALYSIS`) |
| **Node 5: Response** | `gemini-2.0-flash` | Main product analysis + alternative summaries (`MODEL_RESPONSE`) |
| **Node 6: Chat** | `gemini-2.0-flash` | Context-aware conversation with reasoning |
