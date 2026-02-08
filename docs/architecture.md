# System Architecture Documentation

**Project**: Shopping Suggester Agent (CxC 2026)
**Goal**: Visual product analysis, identification, market research, and personalized recommendations.

---

## 🏗️ Architecture Overview

The system uses a **multi-stage agentic pipeline** orchestrated by **LangGraph**, moving from visual detection to deep market intelligence.

### **Stage 1: The Eye (Vision & Intent)**
**Goal**: User uploads an image and asks a question → LLM identifies the target object.
1.  **POST `/api/v1/agent/chat-analyze`**:
    *   Sends image + query to **Gemini 2.0 Flash Vision**.
    *   Identifies target object and returns a **single bounding box**.
2.  **Frontend**: Highlights the object for user confirmation.

### **Stage 2: Discovery (Research & Scouting)**
**Goal**: Gather deep market data and find relevant alternatives.
1.  **Product Researcher**: Searches official pages, reviews (Reddit, YouTube), and pricing (Tavily + SerpAPI).
2.  **Market Scout**: Performs a **Hybrid Search** (Snowflake Vector Search + Web Search) to find the best alternatives.

### **Stage 3: The Brain (Critique & Scoring)**
**Goal**: Verify authenticity and calculate the value proposition.
1.  **Skeptic Node**: Detects fake reviews and calculates the **Eco Score** (B Corp, materials, durability).
2.  **Analysis Node**: Applies a **Weighted Scoring** model (Price, Quality, Trust, Eco) based on user preferences.
3.  **Merge Node**: Syncs parallel outputs for final aggregation.

### **Stage 4: Interaction (Chat & Response)**
**Goal**: Communicate results and handle follow-up queries.
1.  **Response Node**: Generates the final human-like recommendation and verdict.
2.  **Chat Node**: Extracts new user preferences (e.g., "Find sustainable options") and triggers loops back to Research or Analysis.

### **System Orchestration Flow**

```
placeholder image
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
    *   **Sustainability Researcher**: Uses **Tavily** to search for company B Corp status, material sustainability, and ethical manufacturing.
*   **Caching**: Results cached in Snowflake (Tavily: 1 hour TTL, SerpAPI: 15 min TTL, Eco: 2 hour TTL).

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
    3.  **Eco-Scoring**: Evaluates sustainability research data to assign an **Eco Score (0.0 - 1.0)**.
        *   **Criteria**: B Corp certification, use of recycled materials, durability, and company CSR reputation.
    4.  **Cross-Exam**: Check if the "Alternates" suggested by the Scout hold up to scrutiny.

### **Node 4: Analysis & Synthesis (The "Brain")**
*   **Input**: Product Data + Contextual Scout Data + Risk Report.
*   **Agent**: **Analyst Agent** (Gemini 2.0 Flash).
*   **Execution**: Runs **in parallel** with Node 3 (Skeptic). Both outputs are merged before Response node.
*   **Logic**:
    1.  **Preference Loading**: Retrieves explicit user weights.
    2.  **Weighted Scoring**: Calculates a final match score (0-100) for each product based on price, quality, trust, and **sustainability**.
    3.  **Eco-Weighting**: Integrates the `eco_score` weighed by the user's `eco_friendly` preference (default: 0.3 weight).
    4.  **Ranking**: Sorts all products to determine the best recommendation.

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
| **Node 3: Skeptic** | `gemini-2.0-flash` | Deep reasoning for fake review detection and **Eco-Scoring** (B Corp, materials). |
| **Node 4: Analysis** | `gemini-2.0-flash` | Complex multi-factor scoring and ranking |
| **Node 5: Response** | `gemini-2.0-flash` | Fast formatting and data aggregation |
| **Node 6: Chat** | `gemini-2.0-flash` | Intent classification, preference extraction, and session routing. Technologies: Postgres (preference storage), Snowflake (filtered vector search). |
