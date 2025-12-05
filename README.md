# AI Chatbot Platform

This repo hosts four independent FastAPI backends (Claims, HR, Sales Fiber, Sales Motor) plus a Next.js frontend. Use this guide to run everything locally, deploy with Docker/Kubernetes (AKS-ready), and extend the system with new endpoints.

---

## 1. Prerequisites

- Python 3.11+
- Node.js 18+ and npm
- Azure OpenAI credentials (all backends)
- Optional integrations per service:
  - Claims: Azure SQL, Azure Cognitive Search, Neo4j
  - HR & Sales Fiber: Azure Cosmos DB
  - HR & Sales Motor: Azure File Share
  - Sales Motor: Azure OpenAI embeddings
- Docker + Docker Compose (for container testing)
- kubectl & access to an AKS cluster (for K8s deployment)

Create `.env` files inside each backend directory (and `frontend/.env.local`) with the necessary secrets. Copy the structure from `backend/<service>/requirements` or directly from your deployment secrets.

---

## 2. Running Locally (no Docker)

### Claims planner (`backend/claim`, default port 8000)
```bash
cd backend/claim
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt  # on Linux/Mac: .venv/bin/pip
.venv/Scripts/python run_local.py
```

> Only the Claims service ships with a helper `run_local.py`. For every other backend, launch Uvicorn directly as shown below (feel free to add your own helper script if you prefer).

### HR planner (`backend/hr`, default port 8001)
```bash
cd backend/hr
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Sales Fiber (`backend/sales-fiber`, default port 8002)
```bash
cd backend/sales-fiber
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### Sales Motor (`backend/sales-motor`, default port 8003)
```bash
cd backend/sales-motor
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

### Frontend (`frontend`, default port 3000)
```bash
cd frontend
npm install
npm run dev
```

> On Windows replace `.venv/Scripts/...` with `.venv\Scripts\...`.

---

## 3. Running with Docker / Docker Compose

1. Populate environment variables directly in `docker-compose.yml` or leverage Docker secrets.
2. Run `docker compose up --build` (or `docker-compose up --build`).
3. The containers expose:
   - HR: `8000`, Sales Fiber: `8002`, Sales Motor: `8003`, Claim: `8004`, Frontend: `3000`.
4. Stop with `docker compose down`.

> Each backend has its own `Dockerfile` inside `backend/<service>`.

---

## 4. Deploying to AKS (Kubernetes)

Kubernetes manifests live under `k8/`. The repo includes separate deployments/services plus an ingress.

1. Ensure every secret referenced in `k8/secret.yaml` exists (update values as needed).
2. Customize per-service deployments (`k8/claim.yaml`, `k8/hr.yaml`, `k8/motor.yaml`, `k8/fiber.yaml`, `k8/frontend.yaml`).
3. Apply everything with:
   ```bash
   kubectl apply -k k8
   ```
4. Verify pods: `kubectl get pods`.
5. Expose via ingress (`k8/ingress.yaml`) or use LoadBalancer services depending on cluster strategy.

---

## 5. Adding a New Backend Endpoint

### Option A – extend an existing service

1. **Pick the service** (claim/hr/sales-fiber/sales-motor) and open its `main.py`.
2. **Define schemas**: add new `BaseModel` request/response classes if needed.
3. **Implement the route** using FastAPI decorators (`@app.get/post/...`). Reuse existing plugins or register new ones inside the startup/lifespan block.
4. **Update prompts/plugins** if the agent must call new tools.
5. **Document inputs/outputs** in this README or a service-specific doc.
6. **Test locally** via `curl`/`httpie` or the Swagger UI (`http://localhost:<port>/docs`).
7. **Wire the frontend** (see next section) if the UI should consume the new route.

### Option B – add an entirely new backend service

1. **Create a folder:** `backend/<service-name>/`.
   - `main.py` – FastAPI entry point (copy from another service as a starting point).
   - `prompts.py` – system prompt / instructions.
   - `requirements.txt` – service-specific dependencies.
   - `Dockerfile` – optional but recommended for parity with existing services.
2. **Update imports and env vars** so the new service loads its own plugins/tools (SQL, search, etc.) and reads unique environment variable names (`AZURE_OPENAI_*`, `MY_SERVICE_*`, etc.).
3. **Expose standard routes:** `/chat`, `/health`, and any custom endpoints the frontend needs.
4. **Register in Docker Compose:** add a new service block with build context, port mapping, and environment variables.
5. **Add Kubernetes manifests:** duplicate one of the existing `k8/*.yaml` files, tweak labels, images, secrets, and include it in `k8/kustomization.yaml`.
6. **Frontend integration for two chat windows (or more):**
   - Add rewrites in `frontend/next.config.ts`, e.g.:
     ```ts
     {
       source: "/api/myservice/chat",
       destination: `${process.env.BACKEND_DOMAIN_MYSERVICE}/chat`,
     }
     ```
   - Extend `frontend/.env.local` with `BACKEND_DOMAIN_MYSERVICE`.
   - Create a new page under `frontend/app/myservice/page.tsx`. If you need two chat windows on the same page (e.g., comparing two services), render the chatbox component twice with different `useSendQuery` hooks or pass a `chatRoute` prop so each instance talks to a different `/api/...` path.
   - Update `frontend/hooks/useSendQuery.ts` (or create a dedicated hook) so it routes queries based on the pathname or passed-in service key.
   - Ensure any shared state (React Query caches, local session IDs) distinguishes between the two chat windows (e.g., `session_id_myservice_a`, `session_id_myservice_b`).
7. **Document environment variables** and update this README so others know how to run the new service locally, in Docker, and on AKS.
8. **Test end-to-end**: run the backend locally, confirm both chat windows talk to the right endpoints, then validate via Docker Compose and Kubernetes.

---

## 6. Adding a New Frontend Endpoint / Page

1. **Backend destination**: confirm the path you need to call.
2. **Proxy & routing**:
   - Edit `frontend/next.config.ts` to add a rewrite, e.g.:
     ```ts
     {
       source: "/api/myfeature/chat",
       destination: `${process.env.BACKEND_DOMAIN_MYFEATURE}/chat`,
     }
     ```
   - Add `BACKEND_DOMAIN_MYFEATURE` to `frontend/.env.local`.
3. **Hook / fetch logic**:
   - Update `frontend/hooks/useSendQuery.ts` (or create a new hook) so the correct `/api/...` endpoint is called based on the page.
4. **UI**:
   - Add a page under `frontend/app/.../page.tsx` or extend existing components inside `frontend/components`.
5. **Types / state**: adjust `frontend/lib/types.ts`, `state.ts`, or React Query providers as needed.
6. **Test** by running `npm run dev` and confirming the UI reaches the backend through `/api/...`.

---

## 7. Testing Checklist

- **Local**: hit `http://localhost:<port>/health` for each backend, send sample `/chat` payloads with `curl`, and verify the frontend renders.
- **Docker**: `docker compose logs -f` to ensure containers are healthy; run `curl http://localhost:8004/health` etc.
- **AKS**: `kubectl logs`, `kubectl port-forward`, or hit the ingress endpoint. Run readiness checks before promoting changes.

---

## 8. Useful Tips

- Keep `.env` files out of source control (`.gitignore` already covers this).
- When adding endpoints, include sample requests/responses so QA can validate quickly.
- Use `requirements.txt` in each backend to lock dependencies; run `pip freeze > requirements.txt` after upgrades.
- For long-running local development sessions, start services in separate terminals to see logs clearly.

Happy building! 🎉

