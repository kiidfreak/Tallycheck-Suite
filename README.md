# Omni — Monorepo Architecture

![coverage](./badges/coverage.svg)

> One repository, many applications, one design system, one backend.
> **Omni** is the home for all Adept Technologies web applications. The first
> application is **Intranet** 
> Omni is **full-stack and polyglot**: an **Angular** frontend tier and a shared
> **Python Flask + PostgreSQL** backend tier, wired together for local dev with
> **Docker Compose**.

---

## Quick start — running the app

```bash
# install dependencies (once)
npm install

# serve the intranet frontend
npx nx serve intranet            # → http://localhost:4200
```

Other common commands:

```bash
npx nx build intranet              # production build of a single app
npx nx affected -t lint test build # only what your change touched
npx nx graph                       # visualise the project graph
```

Run the **whole stack** (Postgres + Flask API + intranet) with Docker:

```bash
cp .env.example .env        # set POSTGRES_*, DATABASE_URL, JWT_SECRET
docker compose up --build   # postgres + api + intranet, wired together
```

> Full command reference is in [§9 Common commands](#9-common-commands).

---

## 1. Goals

| Goal | How Omni delivers it |
|------|----------------------|
| **One look & feel** | A single design-token + component library (`libs/theme`, `libs/ui`) consumed by every app, so Intranet, and every app after it, look identical by default. |
| **Don't repeat yourself** | 
Auth, the app shell (sidebar/header), utilities, and data-access live in shared `libs/*` — apps compose them rather than re-implement them. |
| **Independent apps, shared core** | Each app under `apps/*` builds, serves, and deploys on its own, but pulls from the same core. |
| **Scales to N apps** | Adding the 2nd, 3rd, 10th app is `nx g @nx/angular:app <name>` — no new toolchain, no copy-paste. |
| **Fast, cached builds** | Nx only rebuilds/tests what actually changed (affected graph + computation cache). |

---

## 2. Technology choices

**Frontend tier**

| Concern | Choice | Why |
|---------|--------|-----|
| Monorepo tool | **Nx** | The de-facto standard for Angular monorepos: project graph, affected commands, generators, caching. |
| Framework | **Angular** (standalone components) | The target stack. Standalone components/routing — no NgModules boilerplate. |
| Language | **TypeScript** (strict) | One `tsconfig.base.json` with path aliases shared across all projects. |
| Styling | **SCSS + CSS custom properties** | The existing `colors_and_type.css` tokens port 1:1 into `libs/theme`. Components consume `var(--adept-*)` tokens — identical visual output to the prototype. |
| Icons | **lucide-angular** | The `lucide` icon set, as an Angular package. |
| State (per app) | Angular signals + services | Lightweight; matches the prototype's local-state model. Promote to a `data-access` lib when shared. |
| Frontend testing | Jest (unit) + Playwright (e2e) | Nx defaults. |

**Backend tier**

| Concern | Choice | Why |
|---------|--------|-----|
| API framework | **Python Flask** | Lightweight WSGI framework. **One backend per app**, co-located at `apps/<app>/backend/`. |
| API structure | **Flask + blueprints** | Domain blueprints (e.g. `auth`) registered on the app; shared Python code lives in `libs/py-auth`. |
| ORM | **SQLAlchemy** (via **Flask-SQLAlchemy**) | The standard Python ORM. Intranet models: `Employee` (UUID), `Department`, `Role`. |
| Migrations | **Alembic** (via **Flask-Migrate**) | Versioned, reviewable schema changes alongside the code (initial revision committed). |
| Database | **PostgreSQL** | One database per app (intranet → `omni_intranet`). |
| Auth | **Auth0** (RS256 / JWKS) | The SPA logs in via Auth0; the backend verifies Bearer tokens with `omni_auth.verify_jwt`. Replaces the prototype's mock `sessionStorage` auth. |
| Backend testing | **pytest** | Standard Python test runner. |

**Platform**

| Concern | Choice | Why |
|---------|--------|-----|
| Containerization | **Docker** | One image per deployable (each app's backend; frontends served via nginx/CDN). |
| Local orchestration | **Docker Compose** | Per-app `apps/<app>/docker-compose.yml` brings up that app's Postgres + backend. |

> **Polyglot note.** Nx manages the JavaScript/Angular side. Each app's Python backend
> lives in `apps/<app>/backend/` with its own `requirements.txt` and virtualenv — it is
> **not** an Nx-built project; run it with `flask`/`pytest`/`docker compose` directly.
> Shared Python (e.g. Auth0 verification) is an installable package in `libs/py-auth`.

## 3. Folder structure

```
omni-apps/
├── README.md                       ← this document — architecture, quick start, commands
├── package.json                    ← JS dependency manifest (frontend / Nx side)
├── nx.json                         ← Nx workspace + task-runner config
├── tsconfig.base.json              ← shared compiler options + path aliases (@omni/*)
├── .prettierrc · .editorconfig · .gitignore
│
├── apps/                           ← deployable applications (one folder each)
│   ├── intranet/                   ← APP #1 — full-stack (frontend + co-located backend)
│   │   ├── src/                    ← Angular FRONTEND (the Nx project)
│   │   │   ├── app/
│   │   │   │   ├── features/       ← one folder per screen (home, call-centre, ai, …)
│   │   │   │   ├── app.routes.ts   ← route table + auth guard + role gating
│   │   │   │   └── app.component.ts← root: <omni-shell> wrapping <router-outlet>
│   │   │   ├── styles.scss         ← imports @omni/theme tokens, then app overrides
│   │   │   ├── index.html
│   │   │   └── main.ts
│   │   ├── project.json            ← Nx build/serve/test targets for the Angular app
│   │   │
│   │   ├── backend/                ← Python Flask BACKEND (per app, not Nx-built)
│   │   │   ├── app.py              ← Flask app: config, db, registers /auth blueprint
│   │   │   ├── models.py           ← SQLAlchemy: Employee (UUID), Department, Role
│   │   │   ├── auth_routes.py      ← Auth0-protected blueprint (/auth/me, /auth/sync)
│   │   │   ├── migrations/         ← Alembic / Flask-Migrate revisions (initial schema in)
│   │   │   ├── requirements.txt
│   │   │   ├── Dockerfile
│   │   │   └── .env.example        ← DATABASE_URL, AUTH0_DOMAIN, AUTH0_AUDIENCE
│   │   │
│   │   └── docker-compose.yml      ← per-app stack: postgres (:5433) + backend (:8001)
│   │
│   └── (future apps live here: e.g. apps/partner-portal, apps/ops-console …)
│
├── libs/                           ← shared, versioned-together code (the "core")
│   ├── theme/                      ← DESIGN TOKENS — the single source of styling truth
│   │   └── src/styles/
│   │       ├── tokens.scss         ← brand colors, type, spacing, radii, shadows (from colors_and_type.css)
│   │       └── index.scss          ← @forward tokens + base resets
│   ├── ui/                         ← DESIGN-SYSTEM COMPONENTS (Card, Button, Pill, StatCard, Avatar…)
│   │   └── src/                    ← standalone Angular components, framework for every app's UI
│   ├── shell/                      ← APP CHROME — Sidebar + Header + layout shell (<omni-shell>)
│   │   └── src/
│   ├── auth/                       ← frontend auth: session, login, role model, guards
│   │   └── src/
│   ├── py-auth/                    ← shared PYTHON auth (Auth0 JWT verification)
│   │   └── omni_auth/              ← `import omni_auth` from any app backend
│   └── util/                       ← framework-agnostic helpers (date/format/storage)
│       └── src/
│
└── tools/                          ← workspace scripts, generators, CI helpers
```

> **Backend topology.** Each app owns its backend, co-located under `apps/<app>/backend/`
> (mirrors the source repo). Cross-backend Python is shared via `libs/py-auth`. This
> replaces the earlier single-shared-`apps/api` sketch.

### Why `apps/` vs `libs/`

- **`apps/*`** are *thin*. An app is routing + screen composition + app-specific glue.
  It owns no design tokens and few primitives — it consumes them.
- **`libs/*`** hold everything meant to be shared. A rule of thumb: **if a second app
  would want it, it belongs in a lib.** The dependency arrow always points
  `app → lib` and `lib → lib`, **never** `lib → app` and never `app → app`.

---

## 4. Path aliases (`@omni/*`)

`tsconfig.base.json` maps every lib to a clean import, so apps never use `../../../`:

| Import | Resolves to | Contains |
|--------|-------------|----------|
| `@omni/theme` | `libs/theme/src` | SCSS tokens (imported in `styles.scss`) |
| `@omni/ui` | `libs/ui/src` | `CardComponent`, `ButtonComponent`, `PillComponent`, … |
| `@omni/shell` | `libs/shell/src` | `ShellComponent`, `SidebarComponent`, `HeaderComponent` |
| `@omni/auth` | `libs/auth/src` | `AuthService`, `authGuard`, `roleGuard`, `ROLES` |
| `@omni/util` | `libs/util/src` | helpers |

Example (an app screen):

```ts
import { CardComponent, ButtonComponent } from '@omni/ui';
import { AuthService } from '@omni/auth';
```

---

## 5. Styling strategy — guaranteeing the same look

The prototype's `colors_and_type.css` `:root` block is the brand contract. In Omni it
becomes `libs/theme/src/styles/tokens.scss` — **the same CSS custom properties, same
hex values, same type scale.** Every app's `styles.scss` does:

```scss
@use '@omni/theme' as *;   // pulls in --adept-navy, --fs-*, --space-*, fonts…
```

Components in `libs/ui` style themselves with `var(--adept-navy-700)`,
`var(--radius-lg)`, etc. — never hard-coded hex. Result: a button in Intranet and a
button in App #5 are byte-identical, and a brand change is a one-file edit in `theme`.

---

## 6. Mapping the prototype → Omni

| Prototype | Omni (Angular) | Location |
|-----------|----------------|----------|
| `colors_and_type.css` | `tokens.scss` | `libs/theme` |
| `shared.jsx` (Card, Button, Pill, StatCard, Avatar, Segmented, EmptyState, Icon) | standalone components | `libs/ui` |
| `Sidebar.jsx`, `Header.jsx` | `SidebarComponent`, `HeaderComponent`, `ShellComponent` | `libs/shell` |
| `LoginView.jsx` + auth gate / `ROLES` / sessionStorage logic in `index.html` | `AuthService`, `authGuard`, `roleGuard`, login route | `libs/auth` + `apps/intranet` |
| `HomeView.jsx`, `CallCentreView.jsx`, `AIView.jsx`, `AppsView.jsx`, `CommunicationView.jsx`, `TeamAttendanceView.jsx`, `CallQAView.jsx`, … | `features/<name>/` components | `apps/intranet` |
| `index.html` `switch(view)` router + role-allow-list | `app.routes.ts` with `canActivate` guards | `apps/intranet` |
| `AttendanceCheckIn.jsx`, `CheckInModal.jsx` | `features/attendance/*` | `apps/intranet` |

---

## 7. Backend & data tier (Flask + PostgreSQL)

One **shared Flask API** (`apps/api`) backs every frontend in the workspace — apps
don't each get their own backend; they call the same service.

**Request flow**

```
Angular app (apps/intranet)
   │  HTTP/JSON  (libs/api-client services)
   ▼
Flask API (apps/api)  ──  blueprints → services → SQLAlchemy models
   │  SQL
   ▼
PostgreSQL
```

**App-factory layout** (`apps/api/app/__init__.py`):

```python
def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or Config)        # DATABASE_URL, SECRET_KEY from env
    db.init_app(app)                                 # Flask-SQLAlchemy
    migrate.init_app(app, db)                        # Flask-Migrate / Alembic
    jwt.init_app(app)
    from .blueprints.auth import bp as auth_bp
    from .blueprints.attendance import bp as attendance_bp
    app.register_blueprint(auth_bp,       url_prefix="/api/auth")
    app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
    return app
```

**Domain model → tables** (initial cut, derived from the prototype):

| Prototype concept | SQLAlchemy model | Notes |
|-------------------|------------------|-------|
| `ROLES` map in `index.html` | `Role`, `User` | role drives nav + access |
| attendance state (check-in/out, shift, location) | `AttendanceRecord` | replaces in-memory `attendance` state |
| Call Centre / QA screens | `Call`, `QaReview` | |
| Communication (chat/email) | `Message`, `Thread` | later |

**Migrations** are versioned with Alembic:

```bash
flask db migrate -m "add attendance_record"   # generate revision
flask db upgrade                               # apply to Postgres
```

**Auth.** The prototype's mock `sessionStorage` login becomes a real
`POST /api/auth/login` issuing a JWT; Angular's `@omni/auth` stores the token and
attaches it via an HTTP interceptor. Role gating stays in the frontend guards **and**
is enforced server-side per blueprint.

**The contract.** `contracts/openapi.yaml` is the agreed request/response shape. The
Flask schemas (Marshmallow) conform to it; `libs/api-client` generates TS types from
it — so a backend change that breaks the contract breaks the frontend build, not prod.

---

## 8. Containerization & local stack (Docker)

`docker-compose.yml` brings the whole stack up with one command:

| Service | Image source | Port | Notes |
|---------|--------------|------|-------|
| `postgres` | `postgres:16` | 5432 | named volume for data; creds from `.env` |
| `api` | `docker/api.Dockerfile` (gunicorn + Flask) | 5000 | depends_on postgres; runs `flask db upgrade` on boot |
| `intranet` | `docker/intranet.Dockerfile` (build → nginx) | 4200 | proxies `/api` to the `api` service |

```bash
cp .env.example .env        # set POSTGRES_*, DATABASE_URL, JWT_SECRET
docker compose up --build   # postgres + api + intranet, wired together
```

Environment variables (never commit `.env`):

```
POSTGRES_USER=omni
POSTGRES_PASSWORD=change-me
POSTGRES_DB=omni
DATABASE_URL=postgresql+psycopg://omni:change-me@postgres:5432/omni
JWT_SECRET=change-me
```

For production, each service builds an independent image; Postgres is a managed
instance (RDS/Cloud SQL) rather than a container, with `DATABASE_URL` pointed at it.

---

## 9. Common commands

```bash
# install once
npm install

# serve the intranet app
npx nx serve intranet            # → http://localhost:4200

# build a single app for production
npx nx build intranet

# run only what your change affects
npx nx affected -t build test lint

# visualise the project graph
npx nx graph

# scaffold the NEXT app (inherits theme/ui/shell automatically)
npx nx g @nx/angular:app apps/<new-app> --standalone --style=scss

# scaffold a new shared lib
npx nx g @nx/angular:lib libs/<name> --standalone
```

Backend (Python) — run from `apps/api` with its virtualenv active:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
flask db upgrade                 # apply migrations to Postgres
flask run                        # dev server → http://localhost:5000
pytest                           # backend tests
```

Whole stack at once:

```bash
docker compose up --build        # postgres + api + intranet
```

---

## 10. Adding a new application (the playbook)

1. `npx nx g @nx/angular:app apps/<name> --standalone --style=scss`
2. In its `styles.scss`: `@use '@omni/theme' as *;`
3. Wrap routes in `@omni/shell`'s `ShellComponent` and gate them with `@omni/auth` guards.
4. Build screens under `features/*`, composing `@omni/ui` components.
5. The app shares brand, chrome, and auth on day one — you only write what's new.

---

## 11. Boundaries & conventions

- **Dependency direction:** `app → lib`, `lib → lib (lower-level)`. Enforced with Nx
  module-boundary lint tags (`type:app`, `type:feature`, `type:ui`, `type:util`).
- **No cross-app imports.** Shared code is promoted to a lib instead.
- **One backend, many frontends.** Apps share `apps/api`; they never talk to Postgres directly.
- **The contract is law.** Frontend and backend agree through `contracts/openapi.yaml`.
- **Standalone everywhere.** No NgModules; components declare their own imports.
- **Tokens only for color/space/type.** No raw hex in components — always `var(--…)`.
- **One screen = one feature folder.** Keeps `apps/intranet` navigable as it grows.
- **Secrets via env, never committed.** `.env` is gitignored; `.env.example` documents the keys.

---

## 12. Roadmap

**Frontend**
- [x] Monorepo scaffold + architecture (this document)
- [x] `libs/theme` — port design tokens from `colors_and_type.css`
- [x] `apps/intranet` — Angular app generated (Nx), wired to `@omni/theme`, builds green
- [~] `libs/ui` — Button, Card, Pill, StatCard, Avatar ported; Segmented, EmptyState, Icon pending
- [x] `apps/intranet` Home screen — first ported feature, renders the design system
- [ ] `libs/ui` — finish remaining primitives + lucide-angular Icon
- [ ] `libs/shell` + `libs/auth` — sidebar/header + login & role gating
- [ ] `apps/intranet` — port remaining screens (Call Centre → AI → Apps → Comms → Team → QA …)
- [ ] App #2 onward — reuse the core

**Backend & platform** (documented now, built later)
- [ ] `apps/api` — Flask app factory + first blueprint (`auth`)
- [ ] SQLAlchemy models + initial Alembic migration (User, Role, AttendanceRecord)
- [ ] `contracts/openapi.yaml` + generated `libs/api-client`
- [ ] `docker-compose.yml` + Dockerfiles (postgres + api + intranet)
- [ ] Replace mock auth with real JWT login end-to-end
