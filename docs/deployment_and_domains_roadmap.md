# 🌐 Tallycheck Suite — Deployment, Domains & Staging Roadmap

This document outlines the complete domain setup, Cloudflare DNS configuration, multi-environment architecture (Staging vs. Production), and CI/CD deployment roadmap for the **Tallycheck Suite**.

---

## 📌 1. Infrastructure Overview

- **Primary Server**: Contabo VPS (`185.202.239.223`)
- **Operating System**: Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-106-generic x86_64)
- **Production Directory**: `/root/tallycheck`
- **Orchestration**: Docker Compose (`docker-compose.prod.yml`)
- **Reverse Proxy**: Caddy v2 (Automatic Let's Encrypt TLS & HTTP/2)
- **Frontend SPA**: Angular 19 Intranet (`apps/intranet`)
- **Backend API**: Python 3.12 Flask REST Gateway (`apps/intranet/backend`)
- **Database**: PostgreSQL 15 (`omni_intranet_db`)

---

## 🗺️ 2. Domain & Subdomain Mapping Matrix

### Production Domains
| Subdomain / URL | Target Service | Proxy Path / Container | Description |
| :--- | :--- | :--- | :--- |
| **`admin.tallycheck.co.ke`** | Angular Intranet | `frontend:80` (Port `8085`/`8443`) | Primary Admin & Staff Management Portal (Attendance, Departments, SafeChild, Beacons, Reports). |
| **`api.tallycheck.co.ke`** | Flask API Gateway | `backend:5000` (Port `8005`) | Dedicated API Gateway for Mobile Apps (SafeChild QR Scanner, BLE Beacon clock-in) & Third-party integrations. |
| **`tallycheck.co.ke`** / **`www`** | Corporate Website | Website App (`apps/website`) | Public marketing landing page & client onboarding. |

> 💡 **Unified Fallback**: `admin.tallycheck.co.ke/api/v2/*` is also reverse-proxied internally to `backend:5000` by Nginx inside the frontend container. This allows single-domain operation without CORS overhead.

### Proposed Staging Domains
| Subdomain / URL | Target Service | Port / Path | Purpose |
| :--- | :--- | :--- | :--- |
| **`staging.admin.tallycheck.co.ke`** | Angular Intranet (Staging) | `/root/tallycheck-staging` | Pre-release UI testing and feature QA. |
| **`staging.api.tallycheck.co.ke`** | Flask API (Staging) | Port `8006` | Pre-release API endpoint testing against staging database. |

---

## ☁️ 3. Cloudflare DNS & SSL Configuration

In the Cloudflare Dashboard for domain **`tallycheck.co.ke`**:

### DNS Records Table
| Type | Name | IPv4 Target | Proxy Status | SSL Setting |
| :--- | :--- | :--- | :--- | :--- |
| `A` | `admin` | `185.202.239.223` | 🟠 **Proxied** | Full / Full (Strict) |
| `A` | `api` | `185.202.239.223` | 🟠 **Proxied** | Full / Full (Strict) |
| `A` | `staging.admin` | `185.202.239.223` | 🟠 **Proxied** | Full / Full (Strict) |
| `A` | `staging.api` | `185.202.239.223` | 🟠 **Proxied** | Full / Full (Strict) |
| `A` | `@` | `185.202.239.223` | 🟠 **Proxied** | Full |
| `CNAME` | `www` | `tallycheck.co.ke` | 🟠 **Proxied** | Full |

### Recommended Cloudflare Rules
1. **SSL/TLS Mode**: Set to **Full** or **Full (Strict)**.
2. **Always Use HTTPS**: Enabled.
3. **Origin Rules (Optional)**: If routing HTTPS directly to Caddy custom host ports (`8085` / `8443`), create an Origin Rule in Cloudflare rewriting port `443 -> 8443`.

---

## 🏗️ 4. Staging vs. Production Environment Architecture

### Option A: Single VPS Dual-Stack (Recommended for Initial Setup)
Runs Staging and Production side-by-side on the existing VPS without additional server costs:

```
VPS (185.202.239.223)
│
├── /root/tallycheck (Production Stack)
│   ├── Container: omni_intranet_db (DB: omni_intranet)
│   ├── Container: omni_intranet_backend (Port 8005)
│   ├── Container: omni_intranet_frontend
│   └── Container: omni_intranet_caddy (Ports 8085/8443)
│
└── /root/tallycheck-staging (Staging Stack)
    ├── Container: omni_staging_db (DB: omni_intranet_staging)
    ├── Container: omni_staging_backend (Port 8006)
    ├── Container: omni_staging_frontend
    └── Container: omni_staging_caddy (Ports 8086/8444)
```

### Environment Settings Comparison

| Parameter | Staging Environment | Production Environment |
| :--- | :--- | :--- |
| **Git Branch** | `dev` | `main` |
| **Server Path** | `/root/tallycheck-staging` | `/root/tallycheck` |
| **Database Name** | `omni_intranet_staging` | `omni_intranet` |
| **Auth0 Tenant** | `dev-tallycheck.eu.auth0.com` | `tallycheck.eu.auth0.com` |
| **Frontend API URL** | `https://staging.api.tallycheck.co.ke/api/v2` | `https://api.tallycheck.co.ke/api/v2` |
| **Deployment Gate** | Automatic on push to `dev` | **Manual Approval Required** in GitHub Actions |

---

## 🔄 5. CI/CD Workflow Pipeline Target (`.github/workflows/deploy.yml`)

### Proposed Dual-Job CI/CD Structure

```yaml
name: CI/CD — Intranet

on:
  push:
    branches: [main, dev]

jobs:
  build-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npx nx run-many -t lint
      - run: npx nx run-many -t test --passWithNoTests
      - run: npx nx build intranet --configuration=production

  deploy-staging:
    needs: build-test
    if: github.ref == 'refs/heads/dev'
    environment: Staging
    steps:
      # Uploads bundle to /root/tallycheck-staging
      # Rebuilds staging compose stack

  deploy-production:
    needs: build-test
    if: github.ref == 'refs/heads/main'
    environment: Production # Requires Manual Approval in GitHub UI
    steps:
      # Uploads bundle to /root/tallycheck
      # Rebuilds production compose stack
```

---

## 📋 6. Action Items Checklist

- [x] Fix container name conflict error in `deploy.yml` and `docker-compose.prod.yml`.
- [x] Standardize VPS production directory path to `/root/tallycheck`.
- [x] Push CI/CD fix commit `1ebf662` to `main`.
- [ ] Add `admin.tallycheck.co.ke` and `api.tallycheck.co.ke` A records in Cloudflare.
- [ ] Update `/root/tallycheck/Caddyfile` on the VPS with active domain names.
- [ ] (Optional) Provision `/root/tallycheck-staging` and update `deploy.yml` for separate staging branch deploys.
