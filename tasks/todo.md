# Node 6 (Chat) Implementation Tasks

- [ ] **Infrastructure & Persistence**
    - [ ] Create `backend/app/models/session.py` (Session, Message models).
    - [ ] Create `backend/app/schemas/session.py` (Pydantic schemas).
    - [ ] Set up LangGraph Checkpointer (MemorySaver for now, or Postgres).

- [ ] **Agent Graph & State**
    - [ ] Update `AgentState` in `backend/app/agent/state.py` with `chat_history` and `router_decision`.
    - [ ] Create `backend/app/agent/nodes/router.py`.
        - Logic: Classify intent (`new_search`, `chat`, `feedback`, `scout`).
    - [ ] Create `backend/app/agent/nodes/chat.py`.
        - Logic: Handle conversation, extract preference updates.
        - **Feedback Loop**: Update `User` preferences in DB via `preference_service`.
        - **Connection**: If searching/filtering, return state to trigger Scout/Node 4.

- [ ] **Integration with Node 4 (Analysis)**
    - [ ] Ensure Node 4 (`analysis.py`) calls `preference_service.get_user_explicit_preferences` (or merged weights).
    - [ ] Verify "Cold Start": If no DB prefs, Node 4 uses defaults.

- [ ] **API Endpoints**
    - [ ] `backend/app/api/v1/endpoints/sessions.py`.
        - `POST /sessions`: New session.
        - `POST /sessions/{id}/chat`: Main entry point for chat.
            - Loads checkpoint.
            - Runs Graph (starting at Router).
            - Returns answer.

- [ ] **Main Graph (`graph.py`)**
    - [ ] Wire up `router_node` as entry point.
    - [ ] Add conditional edges based on Router output.
    - [ ] Add Persistence configuration.

- [ ] **Verification**
    - [ ] Test Cold Start (New user, no prefs).
    - [ ] Test Preference Update ("I hate red") -> Verify DB update.
    - [ ] Test Re-ranking (Trigger Node 4 with new weights).
