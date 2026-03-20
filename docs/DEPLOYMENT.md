# NyumbaLink — Free Deployment Guide
### Vercel · Render · Supabase · Cloudinary · GitHub Actions

---

## Free Tier at a Glance

| Service         | Platform       | What you get (free)                    | Your URL                                        |
|-----------------|----------------|----------------------------------------|-------------------------------------------------|
| **Frontend**    | Vercel         | Unlimited deploys, 100 GB/month        | `nyumbalink.vercel.app`                         |
| **Backend API** | Render         | 750 hrs/month · 1 service always-on    | `nyumbalink-api.onrender.com`                   |
| **Database**    | Supabase       | 500 MB · 50K row reads/day             | Pooled PostgreSQL connection                    |
| **Cache**       | Upstash        | 10,000 req/day · 256 MB Redis          | `rediss://…upstash.io`                          |
| **Images**      | Cloudinary     | 25 GB storage · 25 GB bandwidth        | `res.cloudinary.com/yourname/…`                 |
| **Email**       | Gmail SMTP     | 500 emails/day via App Password        | `smtp.gmail.com:587`                            |
| **CI/CD**       | GitHub Actions | 2,000 min/month (public repos: ∞)      | Auto-deploys on push to `main`                  |
| **Uptime**      | GitHub Actions | Cron ping every 10 min (EAT hours)     | Keeps Render awake during business hours        |

> **Cold-start warning:** Render free tier sleeps after 15 min of no traffic.
> The included keep-alive cron (`.github/workflows/keep-alive.yml`) pings every
> 10 min during EAT 06:00–23:00 to prevent this during Kenyan business hours.
> Upgrade to **Render Starter ($7/mo)** when you need 24/7 instant response.

---

## What You Need Before Starting

- [ ] GitHub account + NyumbaLink code pushed to a repo
- [ ] Accounts created at: Vercel, Render, Supabase, Upstash, Cloudinary
- [ ] Python 3.12 and Node 20 installed locally
- [ ] Git configured locally

---

## STEP 1 — Supabase (PostgreSQL Database)

### 1a. Create Project

1. Go to **https://supabase.com → New project**
2. Name: `nyumbalink` · Password: generate strong one and **save it**
3. Region: **East Africa (eu-west-2)** or `eu-west-1` (London) — closest to Kenya
4. Wait ~2 min for provisioning

### 1b. Apply the Schema

Open **SQL Editor** in Supabase and paste the full contents of `database/schema.sql`.
Click **Run**. All tables should be created with no errors.

Then paste `database/seed.sql` to set up initial data.

### 1c. Get Your Connection String

Go to: **Supabase → Project Settings → Database → Connection string**

Select **Transaction pooler** (port **6543**) — required for Render:
```
postgresql://postgres.YOURREF:YOURPASSWORD@aws-0-eu-west-2.pooler.supabase.com:6543/postgres
```

Append `?sslmode=require` at the end. Final DATABASE_URL:
```
postgresql://postgres.abc123:YourPass@aws-0-eu-west-2.pooler.supabase.com:6543/postgres?sslmode=require
```

> **Always use port 6543** (Transaction Pooler), not 5432 (Direct connection).

### 1d. Create Admin User Locally

```bash
cd nyumbalink/backend
pip install -r requirements.txt
export DATABASE_URL="postgresql://..."     # your Supabase URL

python scripts/seed.py --email admin@nyumbalink.co.ke --password "YourStrongPass123!"
# Output: ✅  Admin user created: admin@nyumbalink.co.ke
```

---

## STEP 2 — Upstash (Redis Cache)

1. Go to **https://console.upstash.com → Create Database**
2. Name: `nyumbalink-cache` · Region: `us-east-1` · Type: **Regional**
3. After creation, copy the **Redis URL**:
   ```
   rediss://default:YOURTOKEN@cheerful-marmot-12345.upstash.io:6379
   ```
   The `rediss://` (double-s) means TLS — required by Upstash.

---

## STEP 3 — Cloudinary (Image Storage)

1. Sign up at **https://cloudinary.com** (free)
2. From the **Dashboard**, copy:
   - **Cloud Name** (e.g. `dnyumba123`)
   - **API Key**
   - **API Secret**
3. **Settings → Upload → Add upload preset:**
   - Name: `nyumbalink_properties`
   - Signing mode: **Signed**
   - Folder: `nyumbalink/properties`
   - Incoming transformation: `w_1200,h_900,c_limit,q_auto,f_auto`

---

## STEP 4 — Render (Backend API)

### 4a. Connect GitHub

1. Go to **https://render.com → New → Web Service**
2. Connect GitHub → select your NyumbaLink repo
3. Configure:
   - **Name:** `nyumbalink-api`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Plan:** Free

### 4b. Build & Start Commands

| Field | Value |
|-------|-------|
| Build | `pip install --upgrade pip && pip install -r requirements.txt` |
| Start | `flask db upgrade && gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120 --max-requests 500 --access-logfile - --error-logfile -` |

### 4c. Environment Variables

In **Render Dashboard → Environment**, add each key below.
Generate secrets with: `python -c "import secrets; print(secrets.token_hex(32))"`

```
FLASK_ENV               = production
PYTHON_VERSION          = 3.12.0

SECRET_KEY              = [generate 32-char hex — unique]
JWT_SECRET_KEY          = [generate different 32-char hex]

DATABASE_URL            = postgresql://postgres.REF:PASS@HOST:6543/postgres?sslmode=require
REDIS_URL               = rediss://default:TOKEN@HOST.upstash.io:6379

CLOUDINARY_CLOUD_NAME   = your_cloud_name
CLOUDINARY_API_KEY      = your_api_key
CLOUDINARY_API_SECRET   = your_api_secret

MPESA_CONSUMER_KEY      = your_daraja_key
MPESA_CONSUMER_SECRET   = your_daraja_secret
MPESA_SHORTCODE         = 174379
MPESA_PASSKEY           = bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
MPESA_ENVIRONMENT       = sandbox
MPESA_CALLBACK_URL      = https://nyumbalink-api.onrender.com/api/payments/callback

MAIL_SERVER             = smtp.gmail.com
MAIL_PORT               = 587
MAIL_USERNAME           = your.email@gmail.com
MAIL_PASSWORD           = xxxx xxxx xxxx xxxx   (16-char Gmail App Password)
MAIL_DEFAULT_SENDER     = NyumbaLink <your.email@gmail.com>

CORS_ORIGINS            = https://nyumbalink.vercel.app
LOG_LEVEL               = INFO
LOG_DIR                 = /tmp/logs
DEFAULT_PAGE_SIZE       = 12
MAX_PAGE_SIZE           = 50
LISTING_FEE_KES         = 500
```

> **Gmail App Password:** Gmail → Account → Security → 2-Step Verification → App Passwords.
> Select "Mail" + device, copy the 16-char password. Use that, not your regular password.

### 4d. Get Deploy Hook (for GitHub Actions)

**Render → Service → Settings → Deploy Hook** → copy the URL.
You'll add it as a GitHub secret in Step 6.

### 4e. Verify the Deploy

After Render finishes building (~3–5 min):

```bash
# Health check
curl https://nyumbalink-api.onrender.com/api/health
# → {"status":"ok","service":"NyumbaLink API"}

# Swagger UI — open in browser
https://nyumbalink-api.onrender.com/api/docs
```

---

## STEP 5 — Vercel (React Frontend)

### 5a. Import Project

1. **https://vercel.com → Add New Project → Import Git Repository**
2. Select your NyumbaLink repo
3. **Framework Preset:** Create React App
4. **Root Directory:** `frontend`
5. Do NOT click Deploy yet — set env vars first

### 5b. Environment Variables

**Vercel → Project → Settings → Environment Variables**
Apply each to **Production + Preview + Development**:

| Variable | Value |
|----------|-------|
| `REACT_APP_API_URL` | `https://nyumbalink-api.onrender.com/api` |
| `REACT_APP_GOOGLE_MAPS_API_KEY` | Your Google Maps JS API key |
| `REACT_APP_CLOUDINARY_CLOUD_NAME` | Your Cloudinary cloud name |
| `REACT_APP_SITE_NAME` | `NyumbaLink` |
| `REACT_APP_SITE_URL` | `https://nyumbalink.vercel.app` |
| `GENERATE_SOURCEMAP` | `false` |
| `NODE_OPTIONS` | `--max-old-space-size=4096` |

### 5c. Deploy

Go back to your project and click **Deploy**. Build takes ~2 min.

Your site is live at:
```
https://nyumbalink.vercel.app
```

The included `vercel.json` automatically handles:
- `/api/*` → proxied to your Render backend
- `/sitemap.xml`, `/robots.txt` → from the Flask SEO routes
- All static assets → `cache-control: immutable, max-age=31536000`
- SPA fallback → all unknown paths serve `index.html`

---

## STEP 6 — GitHub Actions (CI/CD + Keep-Alive)

### 6a. Add GitHub Secrets

**GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Where to find it |
|--------|-----------------|
| `RENDER_DEPLOY_HOOK_URL` | Render → Service → Settings → Deploy Hook |
| `VERCEL_TOKEN` | Vercel → Account Settings → Tokens → Create Token |
| `VERCEL_ORG_ID` | Vercel → Account Settings → General (Team ID) |
| `VERCEL_PROJECT_ID` | Vercel → Project → Settings → General (Project ID) |

### 6b. CI/CD Pipeline (`.github/workflows/deploy.yml`)

On every push to `main` the pipeline runs:

```
push to main
    │
    ├─ 🧪 Backend tests   (pytest + real Postgres service container)
    ├─ 🏗️ Frontend build  (npm run build — ensures it compiles)
    │
    ├─ 🚀 Deploy backend  → Render deploy hook → wait for /api/health
    ├─ 🌐 Deploy frontend → vercel build → vercel deploy --prod
    │
    └─ 💨 Smoke tests     → hit API + frontend, verify 200 OK
```

On pull requests: tests only + auto-comment with preview URL.

### 6c. Keep-Alive Cron (`.github/workflows/keep-alive.yml`)

Pings `GET /api/health` every 10 minutes during EAT 06:00–23:00 (UTC 03:00–20:00).
Prevents Render from sleeping during Kenyan business hours. Free on public repos.

---

## STEP 7 — Verify Everything Works End-to-End

```bash
API=https://nyumbalink-api.onrender.com

# 1. Health
curl $API/api/health

# 2. Register a test user
curl -X POST $API/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"test1234","role":"seeker"}'

# 3. Login
curl -X POST $API/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test1234"}'

# 4. Browse properties
curl $API/api/properties

# 5. Search
curl "$API/api/search?q=nairobi&category=rent"

# 6. SEO sitemap
curl https://nyumbalink.vercel.app/sitemap.xml | head -20

# 7. Robots
curl https://nyumbalink.vercel.app/robots.txt
```

### Run the pre-deploy checker locally at any time:

```bash
cd backend
python scripts/predeploy_check.py
```

This validates all env vars, tests DB connectivity, Redis, Cloudinary, and SMTP.

---

## STEP 8 — Custom Domain (Optional — Free)

Your free subdomain `nyumbalink.vercel.app` works out of the box.
When you're ready for `nyumbalink.co.ke`:

### On Vercel
1. **Project → Settings → Domains → Add Domain**
2. Add `nyumbalink.co.ke` and `www.nyumbalink.co.ke`
3. Vercel shows you the exact DNS records to set

### On Render
1. **Service → Settings → Custom Domains → Add Custom Domain**
2. Add `api.nyumbalink.co.ke`

### DNS Records (set at your registrar — Safaricom Domains, Namecheap, etc.)

```
Type    Host    Value                              TTL
A       @       76.76.21.21                        3600   ← Vercel
CNAME   www     cname.vercel-dns.com               3600   ← Vercel  
CNAME   api     nyumbalink-api.onrender.com        3600   ← Render
```

### Update Env Vars After Custom Domain

**Render:**
```
CORS_ORIGINS       = https://nyumbalink.co.ke,https://www.nyumbalink.co.ke
MPESA_CALLBACK_URL = https://api.nyumbalink.co.ke/api/payments/callback
```

**Vercel:**
```
REACT_APP_API_URL  = https://api.nyumbalink.co.ke/api
REACT_APP_SITE_URL = https://nyumbalink.co.ke
```

---

## Troubleshooting

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `502 Bad Gateway` on first load | Render cold start | Wait 30 s, retry. Keep-alive cron prevents this during business hours. |
| `CORS error` in browser | `CORS_ORIGINS` missing Vercel URL | Update CORS_ORIGINS on Render → redeploy |
| Images fail to upload | Wrong Cloudinary keys | Re-check API Key + Secret in Render env vars |
| DB connection timeout | Wrong Supabase port | Must use port **6543** (Transaction Pooler), not 5432 |
| `SSL SYSCALL error` | Missing SSL mode | Append `?sslmode=require` to DATABASE_URL |
| Login works locally, fails prod | JWT_SECRET_KEY mismatch | Must be identical in local `.env` and Render env vars |
| Frontend build fails on Vercel | Missing `REACT_APP_*` var | Check all vars are set in Vercel dashboard |
| M-Pesa callback fails | Not HTTPS or not public URL | Must use `https://nyumbalink-api.onrender.com/…` |
| Emails not sending | Gmail password blocked | Use 16-char **App Password**, not regular Gmail password |
| `predeploy_check.py` DB error | Wrong DATABASE_URL format | Format: `postgresql://USER:PASS@HOST:6543/DB?sslmode=require` |

---

## Architecture Diagram

```
Users (Browser / Mobile)
          │
          ▼
┌─────────────────────────────────┐
│        Vercel CDN               │  nyumbalink.vercel.app
│        React SPA                │  (or nyumbalink.co.ke)
│  vercel.json: routes + headers  │
└───────────────┬─────────────────┘
                │  /api/* proxied
                ▼
┌───────────────────────┐    ┌───────────────────────┐
│   Render Free Tier    │◄──►│   Supabase             │
│   Flask + Gunicorn    │    │   PostgreSQL 16         │
│   1 worker            │    │   500 MB free           │
│   auto-sleep/wake     │    └───────────────────────┘
└───────┬───────────────┘
        │
   ┌────┼────────┐
   ▼    ▼        ▼
Upstash  Cloudinary   Gmail SMTP
Redis    Images        + Twilio WhatsApp
(cache)  (CDN served)  (notifications)

GitHub Actions
  ├─ CI: tests on every PR
  ├─ CD: deploy on push to main
  └─ Cron: keep-alive ping every 10 min
```

---

## Upgrade Path (When You Outgrow Free)

| Need | Service | Cost | When to Upgrade |
|------|---------|------|-----------------|
| No cold starts | Render Starter | $7/mo | >100 daily active users |
| More DB storage | Supabase Pro | $25/mo | Approaching 400 MB |
| More Redis ops | Upstash Pay-as-go | ~$0.20/10K req | >10K cache hits/day |
| More bandwidth | Vercel Pro | $20/mo | >100 GB/month |
| More image storage | Cloudinary Starter | $89/mo | >25 GB storage |
| Full-text search | Bonsai ES Sandbox | Free (10K docs) | Immediately available |
| Custom email domain | Resend / Postmark | $20/mo | Professional branding |
