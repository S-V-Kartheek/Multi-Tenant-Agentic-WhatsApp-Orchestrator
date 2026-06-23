# Multi-Tenant WhatsApp Agentic Orchestrator

A production-grade, multi-tenant WhatsApp AI agent built with **FastAPI**, **LangGraph**, **Google Gemini**, and **MongoDB Atlas** — deployed on **GCP Cloud Run**.

---

## 🏗️ Architecture

```
WhatsApp User → Meta Cloud API → Cloud Run (FastAPI + LangGraph)
                                        ↓
                              Gemini 1.5 Flash (tool calling)
                                        ↓
                              MongoDB Atlas (sessions + messages)
                                        ↓
                         Cloud Run (React Dashboard) ← SSE live updates
```

**AI Agent Flow:** Acknowledge → Context Retrieval → LLM Reasoning → Dispatch

---

## 🚀 Quick Start (Local)

### Prerequisites
- Docker + Docker Compose
- Node.js 20+
- Python 3.11+

### 1. Clone & configure
```bash
git clone <your-repo-url>
cd multi-tenant-whatsapp-agent
cp backend/.env.example backend/.env
# Edit backend/.env with your actual credentials
```

### 2. Run locally
```bash
docker-compose up --build
```
- **Backend API:** http://localhost:8080
- **API Docs (Swagger):** http://localhost:8080/docs
- **Frontend Dashboard:** http://localhost:5173

### 3. Seed the database
```bash
cd backend
pip install -r requirements.txt
python seed_data.py
```

### 4. Twilio WhatsApp Sandbox — opt recipients in (IMPORTANT)
The backend sends via the **Twilio WhatsApp Sandbox** number `+14155238886` (configured in `.env`).
A sandbox number can **only** deliver messages to phone numbers that have opted in.
For each number you want to message (broadcasts, bot replies, manual agent replies):
1. From that phone, send a WhatsApp message: `join <your-sandbox-keyword>` to `+14155238886`.
2. Wait for the "You are all set!" confirmation from Twilio.
3. Only then will outbound messages reach that recipient.

If a broadcast or bot reply appears "sent" on the dashboard but never arrives on the
phone, the recipient almost certainly hasn't joined the sandbox (Twilio error `63024`).
Check the Twilio console → Messaging → Logs to confirm.

> Note: Read receipts and typing indicators are no-ops under the Twilio sandbox
> (it doesn't expose those endpoints). The dashboard still shows a "typing…" state
> via the DB log + SSE. For the assignment's native typing-indicator demo, swap
> `app/services/whatsapp.py` + `app/api/webhooks.py` to the Meta Cloud API.

---

## ☁️ GCP Cloud Run Deployment

### Prerequisites
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated
- A GCP project with billing enabled
- Docker installed

### Step 1 — Configure Project ID
Edit `PROJECT_ID` in these files:
- `gcp/setup.sh`
- `gcp/deploy-backend.sh`
- `gcp/deploy-frontend.sh`
- `cloudbuild.yaml` (the `_PROJECT_ID` substitution)

### Step 2 — Run One-Time Setup
```bash
gcloud auth login
bash gcp/setup.sh
```
This will:
- Enable Cloud Run, Cloud Build, Artifact Registry, Secret Manager APIs
- Create the Docker image repository
- Prompt you to enter each secret value securely
- Configure all IAM permissions

### Step 3 — Deploy Backend (First Time)
```bash
bash gcp/deploy-backend.sh
```
Copy the output `Backend URL: https://whatsapp-agent-backend-xxxx-uc.a.run.app`

### Step 4 — Deploy Frontend
```bash
bash gcp/deploy-frontend.sh https://whatsapp-agent-backend-xxxx-uc.a.run.app
```

### Step 5 — Configure Meta Webhook
In your Meta App Dashboard:
- **Callback URL:** `https://whatsapp-agent-backend-xxxx-uc.a.run.app/api/webhooks/whatsapp`
- **Verify Token:** the value you set for `META_VERIFY_TOKEN` in Secret Manager

### Step 6 — Enable Auto CI/CD (Cloud Build)
1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Connect your GitHub repository
3. Create trigger: push to `main` → uses `cloudbuild.yaml`
4. Set substitution variable `_BACKEND_URL` to your backend Cloud Run URL

After this, every `git push` to `main` automatically builds and deploys both services.

---

## 🔑 Environment Variables

| Variable | Where Set | Description |
|---|---|---|
| `MONGO_URI` | GCP Secret Manager | MongoDB Atlas connection string |
| `GEMINI_API_KEY` | GCP Secret Manager | Google AI Studio API key |
| `META_VERIFY_TOKEN` | GCP Secret Manager | Custom webhook verify token |
| `META_APP_SECRET` | GCP Secret Manager | Meta App Secret (webhook security) |
| `META_PHONE_NUMBER_ID_TENANT_A` | GCP Secret Manager | Phone number ID for Tenant A |
| `META_WHATSAPP_TOKEN_TENANT_A` | GCP Secret Manager | Access token for Tenant A |
| `META_PHONE_NUMBER_ID_TENANT_B` | GCP Secret Manager | Phone number ID for Tenant B |
| `META_WHATSAPP_TOKEN_TENANT_B` | GCP Secret Manager | Access token for Tenant B |
| `MONGO_DB_NAME` | Cloud Run env var | `whatsapp_agent` |
| `APP_ENV` | Cloud Run env var | `production` |

---

## 📡 API Documentation

Swagger UI auto-generated at `/docs` when running:
- **Local:** http://localhost:8080/docs
- **Production:** https://your-backend.a.run.app/docs

### Key Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/webhooks/whatsapp` | Meta webhook verification |
| `POST` | `/api/webhooks/whatsapp` | Receive WhatsApp messages |
| `GET` | `/api/tenants` | List all tenants |
| `GET` | `/api/sessions?tenant_id=...` | List chat sessions |
| `GET` | `/api/messages?session_id=...` | Get message thread |
| `POST` | `/api/broadcast` | Send template broadcast |
| `GET` | `/api/sse/{tenant_id}` | SSE live updates stream |

---

## 🤖 LangGraph Agent

4-node pipeline:
1. **Acknowledge** — marks message as read + sends typing indicator
2. **Context Retriever** — loads tenant config + 5-message history from MongoDB
3. **LLM Reasoning** — Gemini 1.5 Flash with 3 tools: `reply_with_text`, `send_product_image`, `send_catalog_document`
4. **Dispatcher** — sends WhatsApp response (text/image/document), logs to DB

Bonus: sentiment score < 0.25 → escalates to `NEEDS_HUMAN` status (no auto-reply, red UI alert)

---

## 🏢 Multi-Tenancy

| | Tenant A | Tenant B |
|---|---|---|
| Brand | Luxury Furniture | Automotive Care |
| Agent | Aria | Max |
| Media | catalog, sofa, chair, showroom | invoice, repair diagram, schedule |

Each tenant has isolated: phone number, access token, system prompt, and media library.

---

## 🔒 Security

- **X-Hub-Signature-256** — HMAC-SHA256 webhook verification (bonus feature)
- **GCP Secret Manager** — all secrets encrypted at rest, audit logged
- **Cloud Run** — no inbound traffic except HTTPS (auto TLS via Google-managed cert)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.111 + Uvicorn |
| AI Agent | LangGraph 0.2 |
| LLM | Google Gemini 1.5 Flash |
| Database | MongoDB Atlas (Motor async) |
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS |
| Animations | Framer Motion |
| Live Updates | Server-Sent Events (SSE) |
| Container Registry | GCP Artifact Registry |
| Deployment | GCP Cloud Run |
| CI/CD | GCP Cloud Build |
| Secrets | GCP Secret Manager |
