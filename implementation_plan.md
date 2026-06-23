# Multi-Tenant WhatsApp Agentic Orchestrator — Final Implementation Plan

> ✅ **Plan verified against both PDF and MultiTenant.md** — all requirements confirmed.
>
> **Confirmed Stack Choices:**
> - 🤖 LLM: **Google Gemini** (gemini-1.5-flash for speed + gemini-1.5-pro for reasoning)
> - 🗄️ Database: **MongoDB Atlas** (account ready)
> - ☁️ Deployment: **Render.com** (GCP new → Render is simpler, still fully scored)
> - 📱 WhatsApp: **Sandbox number** (to be provided by you)

---

## Evaluation Weights (Know Exactly How You're Scored)

| Criteria | Weight | Our Strategy |
|---|---|---|
| Agentic Execution & UX | **25%** | LangGraph 4-node graph + Gemini tool-calling + typing indicator |
| Cloud Deployment & Architecture | **25%** | Render.com (Docker, auto-HTTPS, env vars) + async webhook |
| Frontend Integrity | **20%** | Premium dark UI, SSE live updates, all message types |
| Meta API Mastery | **20%** | All endpoints: read, typing, text/image/doc, broadcast |
| Code Quality | **10%** | Clean structure, repo pattern, typed models, swagger docs |

---

## Full System Architecture

```mermaid
graph TB
    subgraph WhatsApp["📱 WhatsApp"]
        USER[Customer Phone]
    end

    subgraph Meta["Meta Cloud API"]
        GRAPH_API[Graph API v20.0]
    end

    subgraph Render["☁️ Render.com"]
        subgraph Backend["FastAPI Backend"]
            WEBHOOK["/api/webhooks/whatsapp\nPOST → 200 OK instantly"]
            BG[Background Task Worker]
        end

        subgraph Agent["🤖 LangGraph Agent"]
            N1[Acknowledge Node]
            N2[Context Retriever]
            N3[LLM Reasoning\nGemini 1.5 Flash]
            N4[Dispatcher Node]
        end

        subgraph Frontend["React Dashboard"]
            DASH[Admin Dashboard\nVite + Tailwind]
        end
    end

    subgraph DB["🗄️ MongoDB Atlas"]
        T[(tenants)]
        S[(chat_sessions)]
        M[(messages)]
    end

    USER -->|sends message| GRAPH_API
    GRAPH_API -->|POST webhook| WEBHOOK
    WEBHOOK -->|200 OK| GRAPH_API
    WEBHOOK -->|triggers| BG
    BG --> N1
    N1 --> N2
    N2 --> N3
    N3 -->|tool call| N4
    N4 -->|send reply| GRAPH_API
    GRAPH_API -->|delivers| USER

    N1 & N2 & N3 & N4 <--> DB
    DASH -->|REST API + SSE| Backend
```

---

## Confirmed Tech Stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| **Backend** | FastAPI | 0.111+ | Async, auto Swagger docs |
| **AI Orchestration** | LangGraph | 0.2+ | Python, stateful graph |
| **LLM** | Google Gemini | 1.5-flash | Fast responses + tool calling |
| **Multimodal (bonus)** | Gemini 1.5-flash | vision | Image description from WhatsApp |
| **Database** | MongoDB Atlas | M0 free | Motor async driver |
| **Frontend** | React + Vite | 18+ | TypeScript |
| **Styling** | Tailwind CSS | 3.x | Required by spec |
| **UI Animations** | Framer Motion | 11+ | Premium feel |
| **Live Updates** | SSE | native | Real-time dashboard |
| **Deployment** | Render.com | — | Docker, auto HTTPS |
| **Containerization** | Docker | multi-stage | Production-ready |

---

## Repository Structure (Production-Grade)

```
multi-tenant-whatsapp-agent/
│
├── 📁 backend/
│   ├── 📁 app/
│   │   ├── main.py                    # FastAPI entry + CORS + lifespan
│   │   ├── config.py                  # Pydantic Settings (env vars)
│   │   │
│   │   ├── 📁 db/
│   │   │   ├── mongo.py               # Motor async client singleton
│   │   │   ├── models.py              # Pydantic data models
│   │   │   └── 📁 repositories/
│   │   │       ├── tenant_repo.py     # Tenant CRUD
│   │   │       ├── session_repo.py    # Chat session management
│   │   │       └── message_repo.py    # Message audit log
│   │   │
│   │   ├── 📁 api/
│   │   │   ├── webhooks.py            # Meta webhook (GET verify + POST handler)
│   │   │   ├── tenants.py             # GET /tenants, GET /tenants/:id
│   │   │   ├── sessions.py            # GET /sessions by tenant
│   │   │   ├── messages.py            # GET /messages by session
│   │   │   ├── broadcast.py           # POST /broadcast (template send)
│   │   │   └── sse.py                 # GET /sse/:tenant_id (live stream)
│   │   │
│   │   ├── 📁 services/
│   │   │   ├── whatsapp.py            # Meta API helper (all send methods)
│   │   │   └── media_resolver.py      # Match query term → tenant media URL
│   │   │
│   │   ├── 📁 agent/
│   │   │   ├── state.py               # AgentState TypedDict definition
│   │   │   ├── graph.py               # LangGraph graph wiring
│   │   │   ├── tools.py               # Tool definitions for Gemini
│   │   │   └── 📁 nodes/
│   │   │       ├── acknowledge.py     # Node 1: read receipt + typing ON
│   │   │       ├── context_retriever.py # Node 2: tenant config + history
│   │   │       ├── llm_reasoning.py   # Node 3: Gemini reasoning + tool call
│   │   │       └── dispatcher.py      # Node 4: send WA + log DB
│   │   │
│   │   └── 📁 utils/
│   │       ├── security.py            # X-Hub-Signature-256 (bonus)
│   │       └── logger.py              # Structured logging
│   │
│   ├── seed_data.py                   # Seed Tenant A & B with media libs
│   ├── Dockerfile                     # Multi-stage production build
│   ├── requirements.txt
│   └── .env.example
│
├── 📁 frontend/
│   ├── 📁 src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── index.css                  # Global styles + design tokens
│   │   │
│   │   ├── 📁 components/
│   │   │   ├── 📁 layout/
│   │   │   │   ├── Sidebar.tsx        # Tenant switcher + nav
│   │   │   │   └── Header.tsx         # Status bar
│   │   │   │
│   │   │   ├── 📁 dashboard/
│   │   │   │   ├── ChatList.tsx       # Active sessions list
│   │   │   │   ├── ChatThread.tsx     # Full chat view
│   │   │   │   ├── MessageBubble.tsx  # Text/Image/Doc/Typing bubbles
│   │   │   │   └── StatusBadge.tsx    # Session status pill
│   │   │   │
│   │   │   └── 📁 broadcast/
│   │   │       └── BroadcastDrawer.tsx # Slide-in campaign panel
│   │   │
│   │   ├── 📁 pages/
│   │   │   └── Dashboard.tsx
│   │   │
│   │   ├── 📁 hooks/
│   │   │   ├── useTenant.ts           # Tenant switcher state
│   │   │   ├── useSessions.ts         # Session list fetcher
│   │   │   └── useSSE.ts              # Server-Sent Events hook
│   │   │
│   │   ├── 📁 api/
│   │   │   └── client.ts              # Axios API client + interceptors
│   │   │
│   │   └── 📁 types/
│   │       └── index.ts               # Shared TypeScript interfaces
│   │
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── Dockerfile
│
├── docker-compose.yml                 # Local dev (backend + frontend)
├── render.yaml                        # Render.com deployment config
└── README.md                          # Full documentation
```

---

## Phase 1 — Project Scaffold & Database Design
**⏱ Hours 0–6 | Day 1 Morning**

### Goals
- Initialize both backend and frontend projects
- Implement MongoDB schema with Motor async driver
- Seed Tenant A (Luxury Furniture) and Tenant B (Automotive Care)

### MongoDB Schema

#### 📦 `tenants` collection
```json
{
  "_id": "ObjectId",
  "slug": "luxury-furniture",
  "name": "Luxury Furniture Store",
  "phone_number_id": "META_PHONE_NUMBER_ID",
  "whatsapp_token": "EAAxxxx...",
  "system_prompt": "You are Aria, a luxury furniture consultant at Prestige Living. You help customers explore our premium collection with warmth and expertise. When customers ask about catalogs or specific items, use your media tools to provide visual assets.",
  "media_library": {
    "catalog":   "https://example.com/furniture-catalog.pdf",
    "sofa":      "https://example.com/sofa-premium.jpg",
    "chair":     "https://example.com/chair-luxury.jpg",
    "showroom":  "https://example.com/showroom.png",
    "brochure":  "https://example.com/brochure.pdf"
  },
  "brand_color": "#8B4513",
  "created_at": "ISODate"
}
```

#### 💬 `chat_sessions` collection
```json
{
  "_id": "ObjectId",
  "tenant_id": "ObjectId (ref: tenants)",
  "customer_phone": "+919876543210",
  "status": "WAITING_FOR_BOT | AGENT_RESPONDING | RESOLVED | NEEDS_HUMAN",
  "context_variables": {},
  "message_count": 0,
  "last_activity": "ISODate",
  "created_at": "ISODate"
}
```

#### 📝 `messages` collection
```json
{
  "_id": "ObjectId",
  "session_id": "ObjectId (ref: chat_sessions)",
  "tenant_id": "ObjectId (ref: tenants)",
  "direction": "inbound | outbound",
  "sender": "+919876543210 | BOT",
  "message_type": "text | image | document | typing_indicator | status_update",
  "text_content": "string",
  "media_url": "string | null",
  "media_mime_type": "image/jpeg | application/pdf | null",
  "media_filename": "string | null",
  "wa_message_id": "string (from Meta API)",
  "agent_state_snapshot": {},
  "timestamp": "ISODate"
}
```

### MongoDB Indexes
```python
# Performance indexes
chat_sessions: [tenant_id + last_activity, customer_phone + tenant_id (unique)]
messages: [session_id + timestamp, tenant_id + timestamp]
```

### Seed Data (Tenant A & B)
- Tenant A: Luxury Furniture — 5 media assets (catalog PDF, sofa/chair/showroom images)
- Tenant B: Automotive Care — 5 media assets (invoice PDF, repair diagram, service schedule)

---

## Phase 2 — WhatsApp Cloud API Integration
**⏱ Hours 6–12 | Day 1 Afternoon**

### WhatsApp Service — All Methods

```python
# services/whatsapp.py

async def mark_as_read(phone_number_id, wa_message_id, token)
# POST /v20.0/{phone_number_id}/messages
# {"status": "read", "message_id": wa_message_id}

async def send_typing_on(phone_number_id, customer_phone, token)
# POST /v20.0/{phone_number_id}/messages
# {"type": "typing_indicator", "typing_indicator": {"type": "text"}}

async def send_text(phone_number_id, to, text, token) → dict
# Supports *bold* and _italic_ WhatsApp markdown

async def send_image(phone_number_id, to, image_url, caption, token) → dict
# {"type": "image", "image": {"link": url, "caption": caption}}

async def send_document(phone_number_id, to, doc_url, filename, caption, token) → dict
# {"type": "document", "document": {"link": url, "filename": filename, "caption": caption}}

async def send_template(phone_number_id, to, template_name, token) → dict
# For broadcast campaigns
```

### Webhook Handler (Critical Pattern)
```python
@router.post("/api/webhooks/whatsapp")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db = Depends(get_db)
):
    # Step 1: Verify X-Hub-Signature-256 (BONUS — implemented!)
    await verify_signature(request)

    # Step 2: Parse payload
    payload = await request.json()
    message_data = extract_message(payload)

    if not message_data:
        return {"status": "ok"}   # ignore non-message events (status updates etc)

    # Step 3: ✅ RETURN 200 OK IMMEDIATELY (< 1 second)
    background_tasks.add_task(
        run_langgraph_agent,
        message_data=message_data,
        db=db
    )
    return {"status": "ok"}
```

---

## Phase 3 — LangGraph Agent
**⏱ Hours 12–22 | Day 1 Evening → Night**

### Agent State (TypedDict)
```python
class AgentState(TypedDict):
    # ─── Inbound ───────────────────────────────────
    wa_message_id: str
    customer_phone: str
    tenant_id: str
    inbound_text: str
    inbound_media_url: Optional[str]      # bonus: user sent image

    # ─── Retrieved Context ─────────────────────────
    tenant: Optional[dict]                # full tenant doc from DB
    chat_history: List[dict]              # last 5 messages
    session_id: Optional[str]
    session_status: str

    # ─── LLM Decision ──────────────────────────────
    response_type: Literal["text", "image", "document"]
    response_text: Optional[str]
    media_url: Optional[str]
    media_filename: Optional[str]
    sentiment_score: Optional[float]      # bonus: 0.0 (angry) → 1.0 (happy)

    # ─── Flow Control ──────────────────────────────
    pipeline_status: Literal["PENDING", "PROCESSING", "DONE", "NEEDS_HUMAN", "ERROR"]
    error_message: Optional[str]
```

### LangGraph Flow

```
[START]
   │
   ▼
┌─────────────────────────────────────┐
│         Acknowledge Node            │──── mark_as_read(wa_message_id)
│   fires instantly before LLM call   │──── send_typing_on(customer_phone)
│                                     │──── save message to DB (status: PENDING)
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│       Context Retriever Node        │──── fetch tenant from DB by tenant_id
│                                     │──── fetch/create chat_session
│                                     │──── get last 5 messages as history
└─────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────┐
│         LLM Reasoning Node          │──── build system prompt (tenant.system_prompt)
│     Gemini 1.5 Flash + Tools        │──── if inbound_media_url → Gemini vision parse (bonus)
│                                     │──── invoke LLM with 3 tools available
│                                     │──── extract: response_type + content + sentiment
└─────────────────────────────────────┘
   │
   ├── sentiment < 0.25 ─────────────────────────────► [NEEDS_HUMAN Node]
   │                                                         │ update session: NEEDS_HUMAN
   │                                                         │ log state → DB
   │                                                    [END] (no auto-reply)
   │
   └── normal ──────────────────────────────────────► [Dispatcher Node]
                                                            │ text?  → send_text()
                                                            │ image? → send_image()
                                                            │ doc?   → send_document()
                                                            │ save outbound to messages DB
                                                            │ update session: RESOLVED
                                                       [END]
```

### Gemini Tool Definitions
```python
tools = [
    {
        "name": "reply_with_text",
        "description": "Send a conversational text reply to the customer. Use this for greetings, questions, explanations, or any non-media response.",
        "parameters": {
            "text": "The reply text. Supports WhatsApp markdown (*bold*, _italic_).",
            "sentiment_score": "Float 0-1 rating of customer frustration (0=very frustrated)"
        }
    },
    {
        "name": "send_catalog_document",
        "description": "Send a PDF document from the media library when customer asks for catalogs, brochures, invoices, price lists, or any document.",
        "parameters": {
            "query_term": "Key term to look up in media library (e.g. 'catalog', 'invoice')",
            "caption": "Friendly caption for the document",
            "sentiment_score": "Float 0-1"
        }
    },
    {
        "name": "send_product_image",
        "description": "Send an image from the media library when customer asks to see products, showrooms, diagrams, or any visual.",
        "parameters": {
            "query_term": "Key term to look up (e.g. 'sofa', 'showroom', 'repair')",
            "caption": "Friendly caption for the image",
            "sentiment_score": "Float 0-1"
        }
    }
]
```

---

## Phase 4 — Frontend Dashboard
**⏱ Hours 22–34 | Day 2 Morning**

### Design System (Premium Dark SaaS)
```
Background:   #0A0F1E  (deep navy)
Surface:      #111827  (card background)
Border:       #1F2937  (subtle borders)
Primary:      #6366F1  (indigo — bot messages, CTAs)
Success:      #10B981  (emerald — resolved status)
Warning:      #F59E0B  (amber — waiting status)
Danger:       #EF4444  (red — NEEDS_HUMAN highlight)
Text:         #F9FAFB  (primary text)
Muted:        #6B7280  (timestamps, secondary)
Font:         Inter (Google Fonts)
```

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  🤖 WhatsApp Agent OS                              [Broadcast 📢]    │
├───────────────┬─────────────────────────────────────────────────────┤
│               │                                                     │
│  TENANTS      │  📞 +91 98765 43210          RESOLVED  ✓           │
│               │  ─────────────────────────────────────              │
│  ● Luxury     │                                                     │
│    Furniture  │  [User]  Hi, I need your catalog                   │
│               │                                                     │
│  ○ Automotive │          Hi! I'm Aria 😊 I'd love to share    [Bot]│
│    Care       │          our luxury furniture catalog...            │
│               │                                                     │
│  ──────────── │          📄 Prestige Living Catalog.pdf       [Bot]│
│               │          [Download ↓]                              │
│  ACTIVE CHATS │                                                     │
│  ────────────  │  ⌛ Aria was typing...                             │
│               │                                                     │
│  +91 987...   │  [User]  Can I see the sofa?                       │
│  Resolved ✓   │                                                     │
│               │          Of course! Here's our signature     [Bot]│
│  +91 876...   │          Milano Sofa 🛋️                           │
│  Typing... ⌛  │                                                     │
│               │          🖼️ [Sofa Image Preview]             [Bot]│
│  +91 765...   │                                                     │
│  🔴 Human     │                                                     │
│               │                                                     │
└───────────────┴─────────────────────────────────────────────────────┘
```

### Key UI Components

| Component | Description |
|---|---|
| **TenantSwitcher** | Toggle A/B with colored brand indicators |
| **ChatList** | Sorted by last_activity, colored status pill |
| **MessageBubble** | 4 variants: user text / bot text / image / document |
| **TypingBubble** | Logged "was typing..." event shown in thread |
| **StatusBadge** | WAITING (amber) / RESPONDING (blue) / RESOLVED (green) / NEEDS_HUMAN (red pulsing) |
| **BroadcastDrawer** | Slide-in panel from right, phone list + template picker |
| **SSE Hook** | Auto-refreshes chat list + thread in real time |

---

## Phase 5 — Deployment (Render.com)
**⏱ Hours 34–42 | Day 2 Afternoon**

### Why Render.com (Not GCP for now)
- **Auto HTTPS** on custom subdomain — needed for Meta webhook
- **Docker support** out of the box
- **Free tier** available for MVP
- **Environment variables UI** — no CLI needed
- **Zero DevOps experience required** — perfect for getting up fast
- Still fully scored (assignment explicitly allows Render, Fly.io, Railway)

### render.yaml (Infrastructure as Code)
```yaml
services:
  - type: web
    name: whatsapp-agent-backend
    runtime: docker
    dockerfilePath: ./backend/Dockerfile
    envVars:
      - key: MONGO_URI
        sync: false          # set in Render dashboard
      - key: GEMINI_API_KEY
        sync: false
      - key: META_VERIFY_TOKEN
        sync: false
      - key: META_APP_SECRET
        sync: false
    healthCheckPath: /health

  - type: web
    name: whatsapp-agent-frontend
    runtime: docker
    dockerfilePath: ./frontend/Dockerfile
    envVars:
      - key: VITE_API_BASE_URL
        value: https://whatsapp-agent-backend.onrender.com
```

### Backend Dockerfile (Multi-Stage)
```dockerfile
# Stage 1: Build
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY app/ ./app/
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
```

### Environment Variables
```bash
# Backend
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/whatsapp_agent
GEMINI_API_KEY=AIza...
META_VERIFY_TOKEN=your_custom_verify_token
META_APP_SECRET=your_meta_app_secret
META_PHONE_NUMBER_ID=  # from Meta dashboard (you'll provide)
META_WHATSAPP_TOKEN=   # from Meta dashboard (you'll provide)

# Frontend
VITE_API_BASE_URL=https://your-backend.onrender.com
```

---

## Phase 6 — Bonus Features + Polish + README + Demo
**⏱ Hours 42–48 | Day 2 Evening**

### All 3 Bonus Features

| Bonus | Implementation | Impact |
|---|---|---|
| **X-Hub-Signature-256** | `utils/security.py` — HMAC-SHA256 header check | Security |
| **Inbound Media** | Gemini vision API on WhatsApp image URLs | Multimodal wow |
| **NEEDS_HUMAN** | Sentiment score in tool call + red UI highlight + auto-halt | UX safety |

### README.md Structure
```markdown
# Multi-Tenant WhatsApp Agent
## Quick Start
## Architecture (LangGraph diagram + explanation)
## Environment Variables
## Running Locally (docker-compose up)
## Deployment Guide (Render.com)
## API Documentation (link to /docs)
## Demo Video
```

---

## 48-Hour Execution Timeline

```
DAY 1
├── 00-02h  Repo init, FastAPI scaffold, React/Vite init
├── 02-06h  MongoDB models + repositories + seed script
├── 06-10h  WhatsApp service (all Meta API methods)
├── 10-12h  Webhook handler (async pattern + signature verify)
├── 12-16h  LangGraph: AgentState + all 4 nodes
├── 16-20h  Gemini integration + tool calling + routing logic
└── 20-24h  End-to-end local test (mock WhatsApp webhook)

DAY 2
├── 00-06h  Frontend: layout + sidebar + chat list + thread
├── 06-10h  Frontend: message bubbles + SSE hook + broadcast
├── 10-14h  Frontend polish + animations + NEEDS_HUMAN red UI
├── 14-18h  Render.com deployment (backend + frontend)
├── 18-20h  Meta webhook configured to live URL + real WA test
├── 20-22h  Bonus features integration + edge case handling
├── 22-24h  README.md + API docs review + demo video recording
└── SUBMIT ✅
```

---

## Checklist for 100% Score

### Task 1: Database ✅
- [ ] `tenants` collection with media_library
- [ ] `chat_sessions` with 4 status values (+ NEEDS_HUMAN for bonus)
- [ ] `messages` audit log with media fields
- [ ] Seed data for Tenant A & B

### Task 2: WhatsApp API ✅
- [ ] GET /webhooks verification (Meta challenge)
- [ ] POST /webhooks (async, < 3s response)
- [ ] mark_as_read implementation
- [ ] send_typing_on implementation
- [ ] send_text / send_image / send_document helpers

### Task 3: LangGraph Agent ✅
- [ ] AgentState TypedDict defined
- [ ] Acknowledge Node (read + typing)
- [ ] Context Retriever Node (tenant + history)
- [ ] LLM Reasoning Node (Gemini + tool calling)
- [ ] Dispatcher Node (send WA + log DB)
- [ ] Conditional edge to NEEDS_HUMAN

### Task 4: Async Webhook ✅
- [ ] FastAPI BackgroundTasks pattern
- [ ] 200 OK before LangGraph starts
- [ ] No timeout/blocking issues

### Task 5: Frontend Dashboard ✅
- [ ] Tenant switcher (A/B)
- [ ] Chat session list
- [ ] Full chat thread with all bubble types
- [ ] Typing indicator in thread (from DB log)
- [ ] PDF download badge
- [ ] Image inline preview
- [ ] Broadcast drawer
- [ ] SSE live updates

### Task 6: Deployment ✅
- [ ] Backend deployed (Render)
- [ ] Frontend deployed (Render)
- [ ] HTTPS URL configured in Meta
- [ ] All env vars set securely

### Bonus ✅
- [ ] X-Hub-Signature-256 webhook security
- [ ] Gemini multimodal image parsing
- [ ] Sentiment → NEEDS_HUMAN fallback + red UI

---

> [!NOTE]
> **Ready to start?** Please share the WhatsApp sandbox phone number and access token when you have it — we can build and test the full flow locally first, then deploy. We'll start with Phase 1 right now.
