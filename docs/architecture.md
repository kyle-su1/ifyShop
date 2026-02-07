# Agent Workflow Architecture

This document outlines the architecture for the **Shopping Suggester** agent workflow. The system is designed to take a user's visual input (screenshot) and query, identify the product, research it across the web, and provide personalized recommendations based on user preferences.

## 1. High-Level Architecture

The core of the system is a **Multi-Agent System** orchestrated by **LangGraph**. The backend is built with **FastAPI** and deploys to **AWS ECS**.

### Tech Stack Overview
- **Orchestration**: LangGraph
- **LLMs**:
  - **Vision/Parsing**: Gemini 1.5 Pro / Flash, OpenAI GPT-4o, Google Cloud Vision API
  - **Reasoning/Analysis**: Gemini 1.5 Pro (Final Recommendation & Chat)
- **Tools**:
  - **Search**: Tavily API (General search, identifying products)
  - **Pricing**: SerpAPI (Google Shopping data)
  - **Scraping**: LangChain Web Scrapers, Puppeteer
- **Database**: 
  - **Operational**: PostgreSQL (Users, Sessions) OR Snowflake (Hybrid Tables)
  - **Vector/Intelligence**: Snowflake Cortex (using Vector Search for reviews/products) OR Postgres (pgvector)
- **Backend & API**: FastAPI, Docker
- **Frontend**: Next.js, Tailwind CSS
- **Authentication**: Auth0

---

## 2. Agent Workflow (LangGraph)

The workflow is a Directed Acyclic Graph (DAG) managed by LangGraph.

### **Node 1: User Intent & Vision (The "Eye")**
*   **Input**: User uploaded image (Screenshot) + Text Prompt (e.g., "Is this a good deal?").
*   **Tools**: Google Cloud Vision, OpenAI Vision, Gemini Vision.
*   **Responsibilities**:
    1.  **Object Detection**: Identify the primary item in the screenshot.
    2.  **Interactive Selection Data**: Return bounding boxes for identified items so the frontend can display hoverable/selectable regions.
    3.  **Context Extraction**: Read text on screen (OCR) to get price, store name, or model number if visible.
    4.  **Ambiguity Resolution**: If multiple items are present, ask the user for clarification (optional interactive step) or infer based on crop/center.
*   **Output**: Structured Product Query (e.g., `product_name: "Sony WH-1000XM5"`, `bounding_box: [100, 200, 300, 400]`, `context: "Amazon listing"`).

### **Node 2: Discovery Layer (The "Researcher" & "Explorer")**
This phase runs two parallel agents to gather deep data on the target product AND finding broad market context.

### **Node 2a: Product Researcher (The "Deep Dive")**
*   **Input**: Structured Product Query (from Node 1).
*   **Goal**: Gather comprehensive data on the *specific* product identified.
*   **Agents**:
    *   **Search Agent**: Uses **Tavily API** to find the official product page and major retail listings.
    *   **Social/Review Scout**: Uses **Tavily** to find "Reddit threads", "YouTube reviews", and "RTings/Expert reviews".
    *   **Price Checker**: Uses **SerpAPI** to look up current pricing across vendors (Best Buy, Walmart, eBay).
*   **Responsibilities**:
    1.  Identify exact product matches.
    2.  Gather raw text of reviews and discussions for the main product.
*   **Output**: Aggregated raw data (Product Specs, Review URLs, Competitor Prices for Main Item).

### **Node 2b: Market Scout (The "Explorer")**
*   **Input**: Structured Product Query + User Preferences (from State).
*   **Goal**: Find relevant *alternatives* or *competitors* based on the user's needs.
*   **Bahavior**:
    1.  **Contextual Search**: If user values "price", search for "best budget alternative to [Product]". If "quality", search "better than [Product]".
    2.  **Live Market Data**: Unlike a static database, this agent searches the live web for current "Best of 2026" lists and comparisons.
*   **Responsibilities**:
    1.  Identify 2-3 strong competitors.
    2.  Fetch basic pricing and rating for these alternatives.
*   **Output**: List of Alternative Candidates (Name, Price, Reason for selection).

### **Node 3: The Skeptic (Critique & Verification)**
*   **Input**: Raw product data (Main Item) + Alternative Candidates (Scout).
*   **Agent**: **Skeptic Agent** (Gemini 1.5 Pro).
*   **Responsibilities**:
    1.  **Fake Review Detection**: Analyze patterns in reviews for the main product.
    2.  **Deal Verification**: Check if the "sale price" is actually a tactic.
    3.  **Cross-Exam**: Briefly check if the "Alternates" suggested by the Scout actually hold up to scrutiny or if they are just paid placement lists.
*   **Output**: Risk Report (e.g., "High likelihood of fake reviews on Amazon", "Alternative X is actually discontinued").

### **Node 4: Analysis & Synthesis (The "Brain")**
*   **Input**: Product Data + Contextual Scout Data + Risk Report.
*   **Agent**: **Analyst Agent** (Gemini 1.5 Pro).
*   **Responsibilities**:
    1.  **Preference Matching**: Compare product features against user weights.
    2.  **Context Integration**: Combine the "Skeptic" warnings with the "Runner" and "Scout" findings.
    3.  **Alternative Scoring**: Score the main item vs. the discovered alternatives.
*   **Output**: Structured Analysis Object.

### **Node 5: Response Formulation (The "Speaker")**
*   **Input**: Structured Analysis Object.
*   **Model**: **Gemini 1.5 Pro**.
*   **Responsibilities**:
    1.  **Final Recommendation**: Generate a empathetic, human-like summary.
    2.  **Format Output**: JSON for frontend (Verdict, Pros/Cons, Pricing).
*   **Output**: JSON Payload.

### **Node 6: Chat/Refinement Loop (The "Conversation")**
*   **Trigger**: User sends a follow-up message (e.g., "What about the warranty?", "Find a cheaper one").
*   **Input**: Chat History + Previous Context.
*   **Action**: Loop back to **Node 2 (Research)** or **Node 4 (Analysis)** depending on if new data is needed.


---

## 3. Data Flow & Schema

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
The final payload sent to the Next.js frontend.
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

## 4. Backend Routes (Specification for Backend Team)

The backend team needs to implement the following endpoints in FastAPI:

### **Authentication (Auth0 Integration)**
*   `GET /api/v1/auth/login`: Redirects to Auth0.
*   `GET /api/v1/users/me`: Returns current user profile (synced from Auth0 to DB).
*   `PATCH /api/v1/users/preferences`: Update user weighing vectors (Price vs Quality, etc.).

### **Core Workflow**
*   `POST /api/v1/agent/analyze`:
    *   **Input**: `{ "image_base64": "...", "user_query": "Is this good?" }`
    *   **Output**: Full Recommendation JSON (Product, Bounding Boxes, Verdict, Alternatives).
*   `POST /api/v1/agent/chat`:
    *   **Input**: `{ "session_id": "...", "message": "Can you find a cheaper option?" }`
    *   **Output**: Streaming text response or updated JSON data.

### **History & Storage**
*   `GET /api/v1/history`: List past user queries/products.
*   `GET /api/v1/history/{id}`: specific details.

---

## 5. Database Strategy: Snowflake vs. Postgres

### **Opinion**:
For a "Shopping Suggester" that relies heavily on vector search (identifying "similar" products, matching "vibe" of reviews), **Snowflake with Cortex** is a powerful choice, but comes with trade-offs vs. PostgreSQL.

#### **Option A: PostgreSQL + pgvector (Recommended for speed/simplicity)**
*   **Pros**: Open source, free locally (Docker), single database for Auth + Vectors + App Data.
*   **Cons**: Scaling vector search to millions of items requires tuning.

#### **Option B: Snowflake + Cortex (Recommended for "Intelligence")**
*   **Pros**:
    *   **Cortex**: Built-in AI functions (complete/summary) and native Vector Search.
    *   **Scalability**: Handles scraping terabytes of Amazon/Reddit data easily.
    *   **Hybrid Tables**: Can now handle transactional app loads (User auth) with decent speed.
*   **Implementation**:
    *   Use **Snowflake** as the primary data warehouse.
    *   Store **Embeddings** of product reviews in Snowflake tables.
    *   Use **Cortex** functions to query: `VECTOR_COSINE_SIMILARITY()`.

### **Selected Path**:
We will design for **PostgreSQL** as the default for *User/Auth* data (low latency), but support **Snowflake Cortex** as the specific engine for the *Recommendation/Vector* layer if API keys are available.

## 6. Deployment Strategy
*   **Containerization**: Both the FastAPI backend and the LangGraph worker nodes are Dockerized.
*   **Infrastructure**: AWS ECS (Fargate).
*   **Auth**: Auth0 handles JWT generation; Backend verifies tokens.

