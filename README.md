# RentCore Agent Backend

This folder contains a standalone FastAPI agent service that integrates LangChain/LangGraph with RentCore backend APIs.

## What it does
- Exposes a `/chat` endpoint for Copilot/agent requests.
- Routes user prompts to tools (read/write) that call RentCore REST APIs.
- Supports confirmation flows, permission checks, and basic in-memory pending actions.

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r agent/requirements.txt
```

3. Configure environment variables:

```bash
export OPENAI_API_KEY=your_key
export OPENAI_MODEL=gpt-4o-mini
export BACKEND_API_BASE_URL=http://localhost:8000
```

## Run

```bash
uvicorn agent.app.main:app --reload --port 8001
```

## Notes
- The agent expects a Bearer token for protected API calls.
- Pending write actions are stored in memory; use a persistent store for production.

## Backend API (reference)
The agent is designed to work with the Car Agency backend described below.

### Project structure (backend)
```
BE/
├── src/
│   ├── config/
│   ├── controllers/
│   ├── routes/
│   ├── middleware/
│   ├── models/
│   ├── migrations/
│   └── seeders/
├── server.js
├── .env.example
└── package.json
```

### Backend setup (summary)
1. Install dependencies: `npm install`
2. Configure `.env` (copy from `.env.example`):
```
PORT=8000
NODE_ENV=development
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=car_agency
DB_PORT=3306
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
JWT_EXPIRATION=7d
```
3. Run the backend:
   - Development: `npm run dev`
   - Production: `npm start`

### API endpoints (high-level)
- Auth: `/api/auth/register`, `/api/auth/login`, `/api/auth/profile`, `/api/auth/change-password`
- Users: `/api/users`, `/api/users/:id`, `/api/users/role/:role`
- Roles/permissions: `/api/roles`, `/api/roles/me/permissions`, `/api/roles/:role`
- Branches: `/api/branches`, `/api/branches/main`, `/api/branches/status/:status`, `/api/branches/:id`
- Tenant: `/api/tenant`, `/api/tenant/logo`
- Cars: `/api/cars`, `/api/branches/:branchId/cars`, `/api/branches/:branchId/cars/:id`

### RBAC and multi-tenant notes
- JWT contains `tenantId`; all data access is scoped to the tenant.
- Permissions include `canCreate`, `canRead`, `canUpdate`, `canDelete`, plus management permissions.
- Branch managers can only manage cars in their assigned branch; admins/owners can manage any branch.


- `/api/copilotkit` forwards chat requests to `PYTHON_AGENT_URL`.
- `/api/insights` forwards chart insight requests to `PYTHON_AGENT_INSIGHTS_URL`.

## 4) Request shape for chart insights

`POST /insights` accepts a body like:

```json
{
  "type": "series",
  "data": [{ "date": "2026-01-01T00:00:00Z", "value": 120 }],
  "labelKey": "date",
  "valueKey": "value",
  "metricLabel": "Revenue",
  "windowSize": 6,
  "formatter": {
    "valueType": "currency",
    "currency": "USD",
    "maximumFractionDigits": 0,
    "labelType": "date"
  }
}
```

The response is:

```json
{
  "insights": [{ "id": "trend", "text": "...", "tone": "positive" }],
  "source": "python"
}
```