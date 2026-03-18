# RouteMind — Interview Prep Guide

> Study this before any technical interview. All answers are grounded in the actual codebase.

---

## SECTION 1: 30-Second Elevator Pitch

**Core pitch (memorize this):**

> "RouteMind is a full-stack AI travel planner I built from scratch. You give it a city, budget, interests, and how many days — it uses semantic search over a curated database of 70+ cities to find the best matching activities, then runs Google OR-Tools constraint optimization to schedule them respecting opening hours, travel time, and budget. GPT-4o-mini writes personalized travel narratives on top. Users can also refine their itinerary conversationally — 'swap the museum for nightlife' — and the app parses intent with an LLM and slot-fills a real replacement. Built with FastAPI, Next.js 14, PostgreSQL with pgvector, and Redis."

**Tailor by audience:**

| Interviewer | Lead with |
|---|---|
| ML/AI | RAG + pgvector + prompt design for refinement intent parsing |
| Backend | OR-Tools scheduling, Redis rate limiting, JWT auth flow, session migration |
| Frontend | Next.js App Router, Zustand state, Google Maps LoadScript pattern, PDF export |
| System Design | Full pipeline + Redis fail-open strategy + horizontal scalability |

---

## SECTION 2: Architecture Walkthrough

**Full data flow — know this cold:**

```
User form (city, budget, interests, pace, days)
        ↓
Next.js frontend (React + Tailwind, Zustand state)
        ↓  POST /api/v1/plan-itinerary
        │  Headers: X-Session-ID, Authorization: Bearer <JWT>
        ↓
FastAPI backend  [routes.py]
        │
        ├── Redis rate limit check
        │       → key: gen_limit:{session_id}
        │       → INCR with 24h TTL (ANON=3/day, AUTH=5/day)
        │       → Fail-open if Redis unreachable
        │
        ├── RAG Retrieval  [retrieval_service.py]
        │       → Build natural language query from preferences
        │       → text-embedding-3-small → 1536-dim vector
        │       → pgvector <=> cosine similarity → top-50 candidates
        │       → Fallback: full SQL if RAG disabled or pgvector unavailable
        │
        ├── OR-Tools Optimizer  [optimizer.py + scoring.py]
        │       → Score each candidate:
        │           rating(0-40) + category_match(0-30) + cost_fit(0-20)
        │           + duration_fit(0-10) - travel_penalty(2pts/min, uncapped)
        │           + must_visit(+50) / avoid(-100)
        │       → Greedy scheduling per day
        │       → Constraints: no food before 11am, no nightlife before 6pm,
        │           no same-category back-to-back, opening hours, budget rolling total
        │
        ├── OpenAI GPT-4o-mini  [generator.py]
        │       → System: "3-4 sentence trip overview + 2-3 bullet tips. No day recap."
        │       → User: formatted preferences + full day-by-day itinerary
        │       → Returns NarrativeResult
        │
        └── Structured JSON response
                ↓
Frontend renders:
  ├── Day-by-day activity cards
  ├── Google Maps route + clickable markers
  ├── AI Travel Guide narrative
  └── Refine with AI (conversational editing)
```

**Refinement flow:**

```
User: "Replace Day 2 museum with nightlife"
        ↓  POST /api/v1/refine
        │
parse_refinement_intent()  [refinement_service.py]
        → LLM call with JSON output mode
        → System prompt includes candidate activity pool (reduces hallucination)
        → Returns: { action: "replace", day: 2,
                     desired_categories: ["nightlife"],
                     search_query: "bar nightclub lounge" }
        ↓
Google Places API fetch  [places_service.py]
        → Triggered if GOOGLE_PLACES_API_KEY set + venue keyword in message
        → Fetch 15 candidates, re-rank by:
            score = rating × log10(review_count + 1) / (distance_km + 0.5)
        → Top 5 returned
        ↓  (fallback: DB semantic search if Places not available)
        │
apply_refinement()
        → Slot-fills best candidate into that day's schedule
        → Recalculates time blocks and cost totals
        ↓
Updated itinerary JSON returned to frontend
```

---

## SECTION 3: Technical Deep Dives

### 3a. RAG Implementation

**File:** `backend/app/services/retrieval_service.py`

- **Embedding model:** `text-embedding-3-small` (1536 dimensions, OpenAI)
- **Vector store:** PostgreSQL + pgvector extension — NOT a separate vector DB
- **Query construction:** Builds a natural language string from user preferences:
  `"food culture activities in Paris for 3 days, budget moderate, preferring outdoor experiences"`
- **Similarity search:** pgvector's `<=>` cosine distance operator in SQL
- **Top-K:** 50 candidates passed to optimizer (configurable via `RAG_TOP_K`)
- **Fallback:** Standard SQL (all activities for city) if RAG disabled, pgvector missing, or no embeddings stored

**Why pgvector over Pinecone/Weaviate?**
> "pgvector keeps everything in one PostgreSQL instance. At our scale — a few thousand activities across 70 cities — cosine similarity search is fast enough. Adding Pinecone means managing another service, syncing data between two stores, and paying for a second managed DB. The complexity tradeoff isn't worth it here. If we were indexing millions of records, I'd reconsider."

---

### 3b. Scoring Function

**File:** `backend/app/core/scoring.py` — `score_activity()`

| Component | Points | Logic |
|---|---|---|
| Rating | 0–40 | Normalized from 0–5 star rating |
| Category match | 0–30 | 30 if preferred, 5 otherwise |
| Cost fit | 0–20 | Quadratic penalty for over-budget |
| Duration fit | 0–10 | Based on available time in day slot |
| Travel penalty | Uncapped | −2 pts × travel_minutes (Haversine dist → speed by mode) |
| Must-visit | +50 | Hard boost |
| Avoid | −100 | Effectively disqualifies |

**Travel modes:** walking=5 km/h, public transit=25, taxi=30, self-drive=40, mixed=20

**Key design:** The travel penalty is intentionally uncapped. A 4.8-star restaurant 30 minutes away loses 60 points to a 4.5-star one 5 minutes away. This enforces geographic clustering — your day doesn't zigzag across the city.

---

### 3c. OR-Tools Optimizer

**File:** `backend/app/core/optimizer.py`

- **Activities per day by pace:** relaxed=2–3, moderate=3–5, active=5–7
- **Algorithm:** Greedy insertion — pick highest-scoring available activity for each slot
- **Constraint enforcement (hard rules):**
  - Opening hours (handles midnight wrap-around for late-night venues)
  - No food before 11am, no nightlife before 6pm
  - No same-category activities back-to-back (diversity penalty)
  - Budget rolling total per day
  - No duplicate activities across days
- **Optimization score returned (0–1):** (budget utilization + category coverage + avg rating) / 3

---

### 3d. LLM Integration

**Files:** `backend/app/llm/generator.py`, `backend/app/services/refinement_service.py`

**Narrative generation prompt:**
```
System: "You are an expert travel writer. Write a brief 3-4 sentence overview
of the trip, then 2-3 practical bullet tips. Do NOT recap each day —
just high-level narrative and insider advice."

User: [preferences summary] + [formatted day-by-day itinerary]
```

**Refinement intent parsing:**
```
System: "Parse the user's request and return valid JSON only.
Actions: replace, add, remove, reschedule.
Available activities to suggest from: [actual candidate pool list]"

User: "Replace Day 2 museum with something for nightlife"

Output: {
  "action": "replace",
  "day": 2,
  "target_category": "culture",
  "desired_categories": ["nightlife"],
  "search_query": "bar nightclub lounge"
}
```

**Why include the candidate pool in the prompt?** Giving the LLM real activity names from the DB dramatically reduces hallucination — it picks from things that actually exist rather than inventing venues.

**Model choice (GPT-4o-mini):** Narrative writing and intent parsing are not reasoning-heavy tasks. GPT-4o-mini performs equivalently at ~10x lower cost for these use cases.

---

### 3e. Redis Rate Limiting

**File:** `backend/app/api/routes.py` — `_check_and_increment_generation_limit()`

```python
key = f"gen_limit:{session_id}"
count = await redis.incr(key)          # atomic increment
if count == 1:
    await redis.expire(key, 86400)     # 24h TTL set on first use only
if count > limit:                      # ANON=3, AUTH=5
    raise HTTPException(429, "Generation limit reached")
```

**Fail-open strategy:** If Redis is unreachable, the limit check is skipped and the request proceeds. This is intentional — Redis becoming unavailable shouldn't block the core itinerary generation feature. For a paid product, you'd flip this to fail-closed.

---

### 3f. Auth Flow (End-to-End)

**Files:** `backend/app/core/auth.py`, `frontend/app/api/auth/[...nextauth]/route.ts`

1. User clicks "Sign in with Google"
2. NextAuth.js handles the OAuth dance → receives Google tokens
3. NextAuth `signIn` callback: `POST /api/v1/auth/google` with `{ google_id, email, name, avatar_url }`
4. Backend: finds-or-creates User record → signs JWT with `JWT_SECRET_KEY`
5. JWT stored in NextAuth session as `session.accessToken`
6. Every plan request sends `Authorization: Bearer <JWT>` header
7. Backend `get_current_user()` dependency: decode JWT → look up User in DB → inject into endpoint
8. On sign-in: `POST /api/v1/auth/migrate-session` migrates anonymous itineraries to user account

**Session migration:** Anonymous itineraries are stored with `session_id` set, `user_id = null`. On sign-in, backend bulk-updates matching rows to set `user_id`, claiming them under the account.

---

## SECTION 4: Design Decisions & Tradeoffs

| Decision | What I chose | Why | What I'd use at 10x scale |
|---|---|---|---|
| Vector store | pgvector in Postgres | Single DB, no extra service, sufficient for thousands of activities | Pinecone / Weaviate for millions |
| Optimizer | Greedy + OR-Tools fallback | Fast and predictable; OR-Tools for complex multi-constraint cases | Full ILP solver with time budgets |
| LLM model | GPT-4o-mini | 10x cheaper, equivalent quality for narrative + intent parsing | GPT-4o only for complex reasoning |
| Auth | NextAuth + custom backend JWT | NextAuth handles OAuth, backend stays stateless | Same pattern, add refresh tokens |
| Redis fail mode | Fail-open | Availability > strict limiting; Redis outage ≠ blocking core feature | Fail-closed for paid tiers |
| Backend | FastAPI (async Python) | Native async enables parallel LLM + Places API calls | Same, add Celery for background jobs |
| Maps | Google Maps JS API with LoadScript at layout root | Prevents multi-instance React errors; only loaded once | Mapbox if cost becomes an issue |

---

## SECTION 5: 3 Non-Trivial Challenges

### Challenge 1: Session ID Fragmentation (Rate Limits Not Enforcing)

**Problem:** Users could generate unlimited itineraries despite the 3/day limit.

**Symptoms:** Checking Redis showed 5+ different session keys for the same user, each at count 1.

**Root cause:** `get_session_id()` in `session.py` checked Redis for the client-sent session ID, and if not found, silently generated a fresh one. So the client's ID (from localStorage) was always discarded after the first request.

**Fix:** Changed to always trust the client-sent session ID. If it's not in Redis, register it there on first sight. The client's localStorage UUID is now the source of truth.

**Lesson:** For stateless rate limiting, the client-owned token (a UUID in localStorage) is more durable as an identity key than server-generated session handles, because the server can't guarantee continuity across restarts.

---

### Challenge 2: Google OAuth Broke After Adding Rate Limits

**Problem:** After wiring up auth and rate limits, Google OAuth stopped working entirely with `invalid_client (Unauthorized)` errors.

**Root cause (three independent factors):**
1. Next.js dev server was picking a random free port (4800, etc.), but the Google OAuth client only listed `localhost:3000` as an authorized redirect URI
2. The Google OAuth client in Cloud Console had been deleted and recreated, but `.env.local` still had the old client secret
3. `NEXTAUTH_SECRET` was set to a placeholder string, not a proper base64-encoded random value

**Fix:**
- Pinned port: added `-p 3000` to the `next dev` script in `package.json`
- Updated `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to match the new OAuth client
- Generated proper secret: `openssl rand -base64 32`
- Fixed NextAuth `signIn` callback to return `true` instead of `false` when the backend call fails — backend errors shouldn't abort the OAuth flow

**Lesson:** OAuth debugging is always layered. Check each independently: port match, client ID/secret match, redirect URI allowlist, and callback logic. Don't assume it's one thing.

---

### Challenge 3: Places API $23/Day Cost Spike

**Problem:** Google Places API billed $23 in a single day during development.

**Root cause:** Ran bulk enrichment script `enrich_and_topup.py` in dev — it called the Places API ~2,800 times to enrich the activity database. This was a one-time setup cost, not runtime usage.

**Fix:** Deleted all one-time data pipeline scripts from the codebase. Runtime Places API usage is 1–5 calls per refinement request, only when a `GOOGLE_PLACES_API_KEY` is configured.

**Lesson:** Separate one-time data pipeline scripts from runtime application code. Never run bulk API scripts without estimating cost first. One-time setup tools should live outside the main repo or be clearly marked.

---

## SECTION 6: Scaling & v2

### How would you scale RouteMind to 10,000 concurrent users?

> "The architecture already separates concerns cleanly. The main bottlenecks are:
>
> 1. **OpenAI latency** — currently the RAG → optimizer → LLM pipeline is sequential. I'd add streaming so users see the narrative as it's generated, reducing perceived wait time.
> 2. **PostgreSQL** — add read replicas for the activity retrieval queries. pgvector search is read-only and parallelizes well.
> 3. **Redis** — already handles rate limiting atomically. At high load, move to Redis Cluster or Upstash.
> 4. **FastAPI workers** — multiple uvicorn workers behind nginx, or Docker containers with k8s HPA scaling on CPU/request rate.
> 5. **Activity data** — it rarely changes, so a CDN cache layer (Cloudflare Workers or Redis cache with long TTL) for city/activity queries would eliminate most DB reads."

### What's v2?

> "A few high-value additions that the current architecture already supports:
> 1. **Real-time collaboration** — the WebSocket infrastructure is already scaffolded in `backend/app/websocket/`. Two users editing the same itinerary.
> 2. **Flight + hotel integration** — Skyscanner or Booking.com APIs. The backend is fully API-driven, so this is an additive feature.
> 3. **Personalization memory** — store past trips and user ratings, then bias RAG queries toward activity types they liked before.
> 4. **Mobile app** — React Native. The backend is already a clean REST API, no changes needed."

---

## SECTION 7: 10 Interview Questions + Strong Answers

**Q1: "Walk me through how you generate an itinerary."**

Start at the form submission. Go through the full pipeline from memory: POST with session + auth headers → Redis rate limit check → RAG retrieval (semantic embedding + pgvector cosine similarity → top-50) → scoring (100-point composite with travel penalty) → greedy scheduler (pace-based, constraint-enforced) → GPT-4o-mini narrative on top → structured JSON response. Mention OR-Tools as a fallback for complex constraint cases.

---

**Q2: "Why did you use pgvector instead of a dedicated vector database?"**

> "pgvector keeps everything in one PostgreSQL instance. For our scale — a few thousand activities across 70 cities — cosine similarity search is fast enough. A dedicated vector DB like Pinecone would mean managing another service, keeping data in sync across two stores, and paying for another managed database. The operational complexity isn't justified at this scale. If we were embedding millions of records, or needed approximate nearest neighbor at millisecond latency, I'd look at Pinecone or Weaviate."

---

**Q3: "How does your rate limiting work? What happens if Redis goes down?"**

> "I use Redis INCR with a 24-hour TTL. The key is `gen_limit:{session_id}`. On the first request, INCR returns 1 and I set the 24h expiry. Subsequent calls increment. Anonymous users get 3/day, authenticated users get 5/day. If Redis is unreachable, the limit check is skipped and the request proceeds — I chose fail-open because I'd rather users get a few extra free generations during a Redis outage than have itinerary generation completely blocked. For a paid product, I'd flip this to fail-closed."

---

**Q4: "How does the conversational refinement work?"**

Walk through the full refinement flow: user message → `parse_refinement_intent()` with JSON output mode → LLM gets the actual candidate activity pool to reduce hallucination → structured intent returned → if Google Places API is configured and a venue keyword is in the message, fetch real places and re-rank by `rating × log10(reviews) / (distance + 0.5)` → `apply_refinement()` slot-fills the best candidate.

---

**Q5: "What was the hardest bug you fixed in this project?"**

Use Challenge 1 (session ID fragmentation). Hit the problem → symptoms (5 keys at count 1) → root cause (backend generating new IDs, discarding client's) → fix (trust client-sent ID, register on first sight) → lesson (client-owned token is more durable for stateless rate limiting).

---

**Q6: "Walk me through the authentication flow end-to-end."**

Google OAuth → NextAuth handles the dance → `signIn` callback calls `POST /api/v1/auth/google` → backend finds-or-creates User, returns JWT → JWT stored as `session.accessToken` in NextAuth → every plan request sends `Authorization: Bearer <JWT>` → `get_current_user()` dependency decodes JWT, looks up User → if user found, AUTH limit (5/day) applied instead of ANON limit (3/day). On sign-in, `POST /migrate-session` moves anonymous itineraries to the account.

---

**Q7: "How does the scoring function work?"**

100-point composite: 40 for rating (normalized), 30 for category match (preferred vs not), 20 for cost fit (quadratic penalty for over-budget), 10 for duration fit, minus travel penalty (2 pts per minute of travel, uncapped). Must-visit gets +50, avoid gets -100. The uncapped travel penalty is intentional — it clusters activities geographically. A great venue 30 minutes away loses 60 points to an almost-as-good one 5 minutes away.

---

**Q8: "What would you do differently if you rebuilt this?"**

> "Two things. First, streaming responses from day one. The current UX makes users wait for the full LLM call before anything renders — with streaming, you could show the narrative appearing word by word while the map loads. Second, observability earlier. Debugging LLM quality issues without trace logs is painful. I'd add Langfuse or LangSmith for LLM traces and structured logging from the start."

---

**Q9: "How does session migration work when an anonymous user signs in?"**

> "Anonymous users get a UUID generated in their browser's localStorage. Their saved itineraries are stored in the DB with `session_id` set and `user_id` as null. When they sign in, the frontend calls `POST /api/v1/auth/migrate-session` with their session ID as a header. The backend queries for itinerary rows with that `session_id` and `user_id = null`, then bulk-updates them to set `user_id` to the newly authenticated user. Their history migrates seamlessly."

---

**Q10: "How is RouteMind different from just asking ChatGPT to plan a trip?"**

> "ChatGPT hallucinates opening hours, costs, and exact locations — and there's no way to verify them. RouteMind uses real activity data from a curated database with actual coordinates, operating hours, price ranges, and ratings. OR-Tools guarantees the schedule is physically feasible: you won't end up with two activities on opposite sides of the city back-to-back. Budget constraints are enforced per day. The LLM in RouteMind only writes the narrative text — it never makes logistics decisions. It's constrained AI generation, not free-form hallucination."

---

## Quick Reference: Key Files

| Topic | File |
|---|---|
| RAG retrieval | `backend/app/services/retrieval_service.py` |
| Scoring (100-pt function) | `backend/app/core/scoring.py` |
| Scheduler / optimizer | `backend/app/core/optimizer.py` |
| LLM narrative prompts | `backend/app/llm/generator.py` |
| Refinement intent parsing | `backend/app/services/refinement_service.py` |
| Rate limiting + main endpoint | `backend/app/api/routes.py` |
| Auth / JWT | `backend/app/core/auth.py` |
| Session management | `backend/app/core/session.py` |
| Places API re-ranking | `backend/app/services/places_service.py` |
| NextAuth config | `frontend/app/api/auth/[...nextauth]/route.ts` |

---

## Study Plan

1. **Read once** — go through each section end-to-end
2. **Pitch practice** — say the elevator pitch out loud, 30 seconds, no notes
3. **Architecture from memory** — draw the data flow diagram on paper without looking
4. **Challenges out loud** — for each: problem → root cause → fix → lesson (2 min each)
5. **Q&A cold** — have someone ask the 10 questions; answer without looking at notes
6. **Code walk** — open each file in the quick reference table, read 5 minutes each

---

*Built by Gurshaan Singh — [GitHub @Gurshaan10](https://github.com/Gurshaan10) · [LinkedIn](https://linkedin.com/in/gurshaan)*
