# System Architecture Documentation

**Project**: Shopping Suggester Agent (CxC 2026)
**Goal**: Visual product analysis, identification, market research, and personalized recommendations.

---

## 🏗️ Architecture Overview

The system uses a **Two-Stage Pipeline** managed by **LangGraph**.

### Stage 1: Targeted Object Detection (Primary: Chat-Based)

**Goal**: User asks about a specific item → LLM finds and highlights that object.

#### **Option A: Chat-Based Detection (Default)**
1.  **Frontend uploads image** → Chat panel appears.
2.  **User asks a question** (e.g., "What is this phone?" or "Where can I buy this keyboard?").
3.  **POST `/api/v1/agent/chat-analyze`**:
    *   Sends image + user query to **Gemini 2.0 Flash Vision**.
    *   LLM identifies the **target object** from the query.
    *   Returns **single bounding box** for that specific item.
    *   Returns chat response acknowledging the item.
4.  **Frontend**: Highlights the targeted object.
    *   *Latency: ~2-3 seconds.*

#### **Option B: Bounding Box Detection (Fallback)**
> Use this mode via "Start Agent Workflow" button for multi-object detection.

1.  **Frontend uploads image** to `/api/v1/agent/analyze` (flag: `detect_only=True`).
2.  **Vision Node (Gemini 2.0 Flash)**:
    *   Detects **all** objects.
    *   Returns bounding boxes for each.
    *   **STOPS execution**.
3.  **Frontend**: Renders interactive boxes over the image.
    *   User clicks a box to trigger Stage 2.
    *   *Latency: ~2 seconds.*

### Stage 2: Deep Analysis (On-Demand)
**Goal**: Analyze a specific product selected by the user.
1.  **User clicks a bounding box** (Option B) or **chat identifies target** (Option A).
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

#### **Flow Diagram (Chat-Based)**
```
┌──────────────────────────────────────────────────────────────────┐
│                   Chat-Based Object Detection                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   1. User Uploads Image + Asks Question                          │
│      "What is this phone?" or "Where can I buy this?"            │
│                                                                   │
│   2. Chat Analysis (Gemini Vision)                               │
│      ┌─────────────────────────────────────────────────────┐     │
│      │  Image + Query → Gemini → Target Object + BBox      │     │
│      │  Time: ~2-3 seconds                                  │     │
│      └─────────────────────────────────────────────────────┘     │
│                                                                   │
│   3. Frontend Highlights Target + Shows Chat Response            │
│      POST /api/v1/agent/chat-analyze                             │
│                                                                   │
│   4. User Clicks Highlighted Object → Deep Analysis (Stage 2)    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Deep Dive: Agent Nodes

### **Node 1: User Intent & Vision (The "Eye")**
*   **Input**: User uploaded image (Screenshot) + Text Prompt.
*   **Model**: **Gemini 2.0 Flash**.
*   **Responsibilities**:
    1.  **Multi-Object Detection**: Identifies **all** distinct objects/products in the image.
    2.  **High Specificity Identification**: Extracts precise Brand, Model, Color, Version (e.g., "Nike Air Jordan 1 Retro High Blue").
    3.  **Visual Attributes**: Generates keywords for similarity search (e.g., "blue, leather, high-top").
    4.  **Bounding Boxes**: Returns normalized coordinates [ymin, xmin, ymax, xmax] for each object.
    5.  **Context Extraction**: Reads text on screen (OCR).
*   **Output**: Structured Product Query containing a list of `detected_objects` and `visual_attributes`.

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
    *   **SerpAPI**: For real-time pricing and shopping links.
    *   **Snowflake Vector Search**: For internal product catalog similarity (Internal Discovery).
*   **Model**: **Gemini 2.0 Flash** (`gemini-2.0-flash`) for fast candidate extraction.
*   **Strategy**: Hybrid Discovery (Internal + External Fusion).
*   **Vector Feedback Loop**:
    *   Validated external findings (from Tavily) are **upserted** to Snowflake `products` with 3072-dim embeddings.
    *   **Purpose**: Continually expands the internal knowledge base with high-quality findings.
*   **Data Capture**: Extracts `thumbnail` (as image_url), `price_text`, and `purchase_link` from shopping results.
*   **Optimization**: Enrichment is limited to **Top 2** candidates. Reviews are skipped for alternatives (LLM already captures recommendation reasons).

### **Node 3: The Skeptic (Critique & Verification)**
*   **Input**: Raw product data (Main Item) + Alternative Candidates (Scout).
*   **Agent**: **Skeptic Agent** (`gemini-2.0-flash`).
*   **Execution**: Runs **in parallel** with Node 4 (Analysis) for latency optimization.
*   **Responsibilities**:
    1.  **Fake Review Detection**: Analyze patterns in reviews for the main product.
    2.  **Deal Verification**: Check if the "sale price" is actually a tactic.
    3.  **Cross-Exam**: Check if the "Alternates" suggested by the Scout hold up to scrutiny.

### **Node 4: Analysis & Synthesis (The "Brain")**
*   **Input**: Product Data + Contextual Scout Data + Risk Report.
*   **Agent**: **Analyst Agent** (Gemini 2.0 Flash).
*   **Execution**: Runs **in parallel** with Node 3 (Skeptic). Both outputs are merged before Response node.
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
*   **Components**: `backend/app/agent/nodes/router.py`, `backend/app/agent/nodes/chat.py`
*   **Model**: **Gemini 2.0 Flash** for intent classification and preference extraction.
*   **Logic**: Classifies intent into:
    *   `vision_search` → New image uploaded → Node 1
    *   `chat` → General conversation → Respond only
    *   `re_search` → Visual prefs (color, brand) OR specific budget ($120) → Node 2 (Market Scout)
    *   `re_analysis` → General price prefs ("cheaper") → Node 4 (re-weight existing)
*   **Preference Extraction**: Gemini extracts `exclude_colors`, `prefer_colors`, `prefer_brands`, `max_budget`, `price_sensitivity`.
*   **Feedback Loop**:
    *   **Postgres**: Saves preferences to `users.preferences` JSON field.
    *   **Snowflake**: Vector search enhanced with extracted criteria.
    *   **Market Scout**: Queries modified with filters (e.g., "blue keyboard under $120").

---

## 4. Frontend Integration
### **Layout Strategy**
*   **Left Panel**: **Input & Interaction**.
    *   Displays the uploaded/analyzed image.
    *   **Scanning Overlay**: Visual scanning effect during analysis.
    *   **Interactive Bounding Boxes**: Clickable overlays for specific object identification (Google Lens style).
*   **Right Panel**: **Agent Output & Analysis**.
    *   **Main Product Card**: High-highlight display of the identified product with Image, Price, Trust Score, Verdict, and "Buy Now" button.
    *   **Alternatives Grid**: Visual grid of recommended alternatives with images, prices, and "View Item" links.

### **Interactive Bounding Boxes**
The frontend (`DashboardPage.jsx`) uses the `detected_objects` list from the API response to render interactive overlays on the **Left Panel**:

1.  **Rendering**: A `BoundingBoxOverlay` component is mapped over the `detected_objects` array.
2.  **Coordinates**: Gemini returns normalized coordinates (0-1000). The frontend converts these to percentage-based CSS (`top`, `left`, `width`, `height`) to overlay correctly on the responsive image.
3.  **Interaction**: 
    *   **Hover**: Displays object name/confidence.
    *   **Click**: Triggers "Lens" identification for that specific object (future implementation).
4.  **Layout**: The image container uses `flex-shrink-0` to ensure it remains visible.

### **Latency Optimization Strategy**
To ensure the analysis runs within strict time limits:
*   **Parallelism**: Nodes 2 (Research) and 2b (Scout) use `ThreadPoolExecutor` for external API calls. Nodes 3 (Critique) and 4 (Analysis) run in parallel.
*   **Candidate Limiting**: Market Scout limits enrichment to the **Top 2** candidates to prevent API fan-out.
*   **Timeouts**: All parallel executions have strict timeouts (10-20s) to prevent hanging.
*   **Context Pruning**: The "Skeptic" agent only analyzes the Top 5 reviews per product to reduce LLM input tokens.

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
| **Node 1: Vision** | `gemini-2.0-flash` + Google Lens | Hybrid: Gemini for fast detection (Stage 1), Lens for deep identification (Stage 2). |
| **Node 2: Research** | N/A (API calls) | Tavily + SerpAPI, no LLM |
| **Node 2b: Market Scout** | `gemini-2.0-flash` | Fast candidate extraction from search results |
| **Node 3: Skeptic** | `gemini-2.0-flash` | Deep reasoning for fake review detection |
| **Node 4: Analysis** | `gemini-2.0-flash` | Complex multi-factor scoring and ranking |
| **Node 5: Response** | `gemini-2.0-flash` | Fast formatting and data aggregation |
