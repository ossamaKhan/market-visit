# Market Visit Dashboard

Three completely separate portals, each with its own login URL, dashboard,
and nav — no shared/mixed login page.

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # creates your first admin account
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` — a landing page links to all three logins.
`createsuperuser` prompts for an email; if left blank, set one via
`/admin/` before logging in, since login is by email everywhere.

## The three portals

### 1. Field Agent — `/field/login/`
Field agents log in here and land on `/field/dashboard/`.
- **Dashboard** (`/field/dashboard/`) — just their own total visit count.
- **Log Visit** (`/field/log-visit/`) — the full sectioned form.
- Visit details live at `/field/visits/<id>/` (reachable right after
  logging a visit, and by Management clicking through from their list).
- No edit/delete anywhere in this portal — visits are locked once
  submitted; only Admin can delete a log.
- Rejects accounts that only have Management (viewer) access — those
  get pointed to the Management login instead.

### 2. Management — `/management/login/`
Staff or "viewer" accounts log in here and land on `/management/`.
- Filters every visit by **ARM, City, BU, Franchise** (from the full
  uploaded Hierarchy, not just franchises with a logged visit) plus a
  date range.
- **Download PDF** — exports the filtered visits (with comments and both
  photos) as a PDF.
- **Comment on a specific visit** — open any visit's detail page and add
  or update a Management Comment. Field agents can see this comment
  (read-only) on their own visit's detail page, but can't edit it.
- Rejects plain field-agent accounts — they're pointed to the Field
  Agent login instead.

### 3. Admin Portal — `/admin-portal/login/`
Staff only; a valid non-staff login is rejected with an explicit message.
- **Dashboard** (`/admin-portal/`) — quick counts and shortcut cards.
- **Create User** (`/admin-portal/users/create/`) — add a Viewer or Field
  Agent account. You type the email and password yourself — nothing is
  auto-generated here.
- **Manage Users** (`/admin-portal/users/`) — every account, role badge,
  masked password (reveal on click), reset-to-random or set-a-specific-
  password.
- **Visit Logs** (`/admin-portal/visits/`) — browse every logged visit
  and **delete** any of them (with a confirmation step).
- **Upload Hierarchy** / **Hierarchy** (`/admin-portal/hierarchy/...`) —
  upload the franchise hierarchy Excel file and browse what's uploaded.
  This flow still auto-creates field-agent accounts with random
  passwords (see below) — that's intentionally separate from Create
  User, since it's provisioning many ARMs at once from a spreadsheet.

## Log Visit form

1. **Franchise** — dropdown scoped to franchises whose hierarchy email
   matches the logged-in user. Selecting one auto-fetches Region, BU, FR
   Status, FR City, FR Address, ARM Name, ARM Emp #, and Email into a
   read-only box. The visit date is set automatically to today.
2. **Information** — Name, EVC (must start with `03` or `92`, digits
   only), Type (Retailer / DSO / Stall / WIC), BVS (Yes/No), RSO Visit
   (Yes/No), Location (auto-captured via browser geolocation).
3. **Stock Information** — Load Stock range, PSim/NP Sim/E Sim/Data Sim
   stock counts.
4. **Competition** — Average Loading and Average Sim Sales, for Zong and
   Jazz separately.
5. **Visibility** — Fascia, AVH, POS (all Yes/No), Promo Awareness and
   Bundle Awareness (Low/Medium/High).
6. **Comments** — the field agent's own free-text notes (separate from
   Management's comment above).
7. **Photos** — up to 2 image uploads.

## Admin: hierarchy upload & auto-provisioned accounts

Uploading a hierarchy `.xlsx` (headers: `FR ID, Region, BU, FR Status,
FR City, FR Address, ARM Name, ARM Emp #, Email`) upserts `FranchiseRecord`
rows keyed on FR ID, and auto-creates a login (random password) for every
unique email that doesn't already have one. This is separate from Create
User, which never generates a random password.

## Caching & indexing

- `FranchiseRecord.region/bu/fr_city/arm_name/email` and
  `MarketVisit.visit_date/priority/status` are indexed.
- Management's filter-dropdown options are cached for 5 minutes and
  invalidated right after a hierarchy upload.
- Cache backend is `LocMemCache` by default; switch to Redis if you scale
  past one web process (commented-out config in `core/settings.py`).

## Project layout

```
market_visit_dashboard/
├── manage.py
├── requirements.txt
├── core/                  # settings, root urls, landing page (/)
├── accounts/               # Field Agent login/logout, email-based auth backend
├── visits/                 # MarketVisit model, Field Agent dashboard/log-visit/detail
├── hierarchy/               # FranchiseRecord, hierarchy upload, password reset/set
├── reports/                 # Management login/logout/dashboard, PDF export, comments
├── admin_portal/            # Admin login/dashboard, Create/Manage Users, Visit Logs
├── templates/
│   ├── base.html            # Field Agent layout (Bootstrap navbar)
│   ├── detail_base.html      # neutral layout for the shared visit-detail page
│   └── portal_select.html    # landing page linking to all 3 logins
├── static/css/style.css     # shared theme (Bootstrap CSS variables + custom classes)
└── media/visit_photos/      # uploaded visit photos (created at runtime)
```

## Visual theme

Bootstrap 5 (CDN) everywhere, with a custom teal (`#0E7C86`) and amber
(`#F2994A`) theme on top — Manrope for headings, Inter for body text, a
small three-bar "signal" mark next to the wordmark. Each portal has its
own navbar color so they're visually distinct: teal for Field Agent, a
management accent for Management, deep navy for the Admin Portal.

## Switching to Postgres / Supabase

```bash
export DB_ENGINE=django.db.backends.postgresql
export DB_NAME=postgres
export DB_USER=your_supabase_user
export DB_PASSWORD=your_supabase_password
export DB_HOST=your_supabase_host
export DB_PORT=5432
```
Then `pip install psycopg2-binary` and `python manage.py migrate` again.

## Deploying (e.g. to Render)
- Set `DJANGO_DEBUG=False`, `DJANGO_SECRET_KEY=<random>`,
  `DJANGO_ALLOWED_HOSTS=<your-render-domain>`.
- Add `gunicorn` and `whitenoise` for static files; run
  `python manage.py collectstatic` in your build step.
- Switch `CACHES` to Redis if you run more than one web process.

## Mobile / responsive design

Bootstrap's navbar collapses into a hamburger menu on phones, tables
scroll horizontally in their own container, and form inputs use 16px font
so iOS Safari doesn't auto-zoom on focus.
