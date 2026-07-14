# TallyCheck Corporate & School Suite — Monorepo Architecture

![coverage](./badges/coverage.svg)

> **TallyCheck Corporate** is an enterprise-grade, multi-tenant SaaS platform for employee workforce management, BLE beacon presence verification, and **SafeChild** daycare/Sunday school safe pickup tracking.
> 
> Built on a robust **Angular frontend** and a multi-tenant **Python Flask + PostgreSQL backend**, co-located and orchestrated locally using **Docker Compose** and **Nx**.

---

## 🚀 Quick Start — Running the Stack

### 1. Frontend Development Server (Angular)
```bash
# Install dependencies
npm install

# Start the Intranet portal
npx nx serve intranet            # → http://localhost:4200
```

### 2. Backend Development Server (Flask)
```bash
# Navigate to backend folder
cd apps/intranet/backend

# Create virtual environment and install requirements
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Create .env config from example
cp .env.example .env

# Apply database migrations
.venv\Scripts\flask db upgrade

# Run backend development server
.venv\Scripts\flask run --port=5000  # → http://localhost:5000
```

---

## 🏛️ Architecture Details

### 1. Secure Multi-Tenant Schema Isolation
TallyCheck uses **PostgreSQL Schema-based Isolation** (One Schema Per Tenant).
*   **Public Schema**: Houses `public.organizations` (the tenant directory).
*   **Tenant Schema**: When a tenant is resolved (e.g. Daystar University), the backend dynamically scopes all subsequent tables (`employees`, `attendance_records`, `ble_beacons`, `children`, `pickup_tokens`) to `tenant_<org_id>` using a connection-level `search_path` interceptor middleware.
*   **Auth0 Organizations**: Connects corporate and academic Identity Providers (SSO) directly to individual tenant schemas using Auth0 B2B token claims.

### 2. BLE Beacon Proximity Tracking
*   **Hardware Registry**: Register MAC addresses, Major, Minor, and proximity boundaries for BLE beacons.
*   **Department Assignment**: Assign registered beacons to physical offices or rooms to enforce geo-presence verification rules.

### 3. SafeChild Drop-off & Pickup Verification
*   **Single-Use Tokens**: Child drop-off generates a secure, random 4-digit PIN and a signed QR payload.
*   **HMAC-SHA256 Signatures**: QR code payloads are signed with a server-side `SAFECHILD_HMAC_SECRET` to prevent tampering.
*   **IP-Based Rate Limiting**: Verification requests to `/safechild/pickup/verify` are protected by a sliding-window rate limiter to block PIN brute-forcing.

---

## 📂 Folder Structure

```
tallycheck-corporate/
├── apps/
│   └── intranet/                     ← Main portal application
│       ├── src/app/features/
│       │   ├── login/                ← Subdomain name resolution & Auth0 redirect
│       │   ├── beacons/              ← BLE beacon listing & department assignment view
│       │   ├── home/                 ← Dashboard with check-in widgets & active shifts
│       │   └── departments/          ← Organizational structure definition
│       └── backend/                  ← Flask API Gateway
│           ├── migrations/           ← Database migration versions (Alembic)
│           ├── schemas/              ← Serialization schemas (beacons, employees, etc.)
│           ├── utils/
│           │   └── tenant_middleware.py ← Dynamic search_path schema selection middleware
│           ├── auth_routes.py        ← Organization subdomain lookup endpoint
│           ├── beacon_routes.py      ← BLE beacon registry and assignment endpoints
│           └── safechild_routes.py   ← Children list, drop-off logging, and verify APIs
├── libs/
│   ├── auth/                         ← Angular Auth0 organization-aware auth library
│   ├── shell/                        ← Navigation links and main sidebar layouts
│   ├── theme/                        ← Shared SCSS tokens, fonts, and resets
│   └── ui/                           ← Shared premium cards, pills, buttons, and icons
```

---

## 🛠️ Common Platform Commands

```bash
# Run tests
npx nx test intranet

# Generate production build
npx nx build intranet

# Run lint checks
npx nx lint intranet

# View workspace project graph
npx nx graph
```

---

## 🧪 Seeding & Setup for Demos

To test subdomain redirection and Auth0 Organizations locally:
1. Create your organization in the **Auth0 Dashboard** (copy the generated `org_xxxxxxx` ID).
2. Configure **Allowed Callbacks** in your Auth0 Application to point to `http://localhost:4200`.
3. Seed the local organization table using the helper script:
```bash
.venv\Scripts\python scratch/seed_org.py
```
