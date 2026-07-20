# Advanced News & Blog Platform (Django)

A full-featured news/blog platform built with Django 5.2 and PostgreSQL. Includes a
publishing dashboard, category management with dropdown menus, push notifications
(Web Push/VAPID), email newsletters, PWA support, dark mode, SEO tooling
(sitemaps, news sitemap, meta management, AI-assisted content analysis and
internal link suggestions), comments with moderation, and a responsive
BBC-inspired front end.

---

## Requirements

- Python 3.12+
- PostgreSQL 14+ (developed and tested on PostgreSQL 18)
- pip / venv

---

## Quickstart (approx. 15 minutes)

### 1. Create a virtual environment and install dependencies

```bash
python -m venv .venv
# Windows (Git Bash):
source .venv/Scripts/activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Create the PostgreSQL database

Open psql as the postgres superuser and run:

```sql
CREATE DATABASE myblog_db;
CREATE USER myblog_user WITH PASSWORD 'choose_a_password';
GRANT ALL PRIVILEGES ON DATABASE myblog_db TO myblog_user;
ALTER DATABASE myblog_db OWNER TO myblog_user;
```

> The `ALTER ... OWNER` line is required on PostgreSQL 15+ — without it,
> migrations fail with "permission denied for schema public".

Password tip: use letters and numbers only. Avoid `@ : / # '` and spaces —
they can break connection strings.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in every value. At minimum you need `SECRET_KEY`,
the `DB_*` variables, and (for push notifications) the VAPID values —
see the VAPID section below.

Generate a fresh `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Migrate, create your admin user, and run

```bash
python manage.py migrate
python manage.py setup_nltk        # downloads language data for content analysis (one-time)
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000 — the site is running (empty until you add content).

> **Rule of thumb:** after any change to `.env` or to signal files, restart the
> dev server. Environment values and signal registrations are read at startup.

---

## Push Notifications (VAPID keys) — read carefully

Web Push requires a VAPID keypair. **You must generate your own** — the public
and private keys must come from the same generation run; mixing halves from
different runs breaks push silently.

### Generate the keypair

The `py-vapid` package (already in requirements) provides a CLI:

```bash
vapid --gen
```

This creates two files in the current directory:

- `private_key.pem` — keep this file. Move it to the **project root**
  (same folder as `manage.py`). The application loads it by path.
  **Never commit it** (it is already listed in `.gitignore`).
- `public_key.pem`

### Get the public key in application format

The application needs the public key as a base64url string (starts with `B`,
about 87 characters). Print it with:

```bash
vapid --applicationServerKey
```

Copy the output into `.env`:

```
VAPID_PUBLIC_KEY=BOr3...your-87-char-key...
VAPID_ADMIN_EMAIL=you@yourdomain.com
```

### Common mistakes (these WILL break push)

1. **Pasting PEM text into `.env`** — the private key is a *file*
   (`private_key.pem` in the project root), not an environment variable.
2. **Mismatched pair** — regenerating one key without the other. If you ever
   regenerate, replace both, and note that existing browser subscriptions
   become invalid (users must re-subscribe).
3. **Wrong path** — `private_key.pem` must sit next to `manage.py`.

If push fails with `Could not deserialize key data ... invalid length`,
the private key file is malformed or the app is receiving key text instead
of a file path — regenerate with `vapid --gen` and re-place the file.

A `410 Gone` in the logs is normal: it means a browser subscription expired.
The app automatically deactivates those subscriptions.

---

## Email (newsletter + notifications)

The platform sends a newsletter email when a post is published. Configure SMTP
in `.env`. For Gmail:

1. Enable **2-Step Verification** on the Google account
   (required before App Passwords appear).
2. Google Account → Security → **App passwords** → create one
   (name it anything, e.g. "blog").
3. Google shows a 16-character password **once**. Put it in `.env`
   **without spaces**:

```
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=abcdefghijklmnop
DEFAULT_FROM_EMAIL=you@gmail.com
```

Test from the shell:

```bash
python manage.py shell -c "from django.core.mail import send_mail; send_mail('Test','It works',None,['you@gmail.com'])"
```

---

## First-run configuration

1. **Site identity** — log into the dashboard and open Site Settings.
   Set your site name, tagline, and social links. Also set `SITE_NAME` and
   `SITE_URL` in `.env` (used by the PWA manifest and system emails).
2. **Logo** — replace the placeholder logo in `static/images/` with your own,
   then run `python manage.py collectstatic` if serving collected statics.
3. **Categories** — create categories in the dashboard. To build dropdown
   menus in the navbar, give a category a **Parent**: parent categories render
   as "Name ▾" with their children in the dropdown. Categories without
   children render as plain links.
4. **First post** — create a post and set its status to **Published**.
   Only Published posts appear on the site; publishing is also what triggers
   subscriber notifications (in-app, push, and email). Notifications fire
   only on the *transition* to Published — re-saving an already-published
   post does not re-notify subscribers.

### How the home page fills in

The home layout has a featured slot, a trending sidebar, an editor's-picks
sidebar, a recent-articles carousel, and per-category blocks. Sections show
content as it becomes available:

- Mark a post **Featured** to pin it to the featured slot.
- Mark posts **Editor's Pick** to curate that sidebar (otherwise it falls
  back to recent posts).
- Category blocks need 2+ posts for their sidebars to populate
  (1 post fills only the featured slot of that block).

With fewer than ~6 posts, some sections will show empty-state messages —
this is expected and resolves as you publish.

---

## Optional features

- **AI content analysis** (readability, SEO scoring) and **internal link
  suggestions** run locally using NLTK/scikit-learn — no external API or key
  required. Toggles live in `AI_CONTENT_SETTINGS` in settings.
- **Redis cache** — the project supports django-redis. If you do not run
  Redis, switch `CACHES` to local-memory in settings.
- **Social login** (Google/Facebook via django-allauth) — create the provider
  apps in Django admin → Social applications, and attach them to your Site
  (`SITE_ID` in settings must match a row in the Sites table). Exactly one
  app per provider per site.

---

## Deploying to production

1. In `.env`:
   ```
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   SITE_URL=https://yourdomain.com
   ```
   Note `CSRF_TRUSTED_ORIGINS` requires the scheme (`https://`);
   `ALLOWED_HOSTS` must not include it.
2. Collect static files:
   ```bash
   python manage.py collectstatic
   ```
   (WhiteNoise is configured for serving statics.)
3. Run behind a production server (gunicorn/uwsgi + nginx, or your host's
   equivalent). HTTPS is required for push notifications and PWA install.
4. Update the Django **Sites** entry (admin → Sites) to your real domain,
   and confirm `SITE_ID` points at it — social login and absolute URLs
   depend on this.

### Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Every page returns 400 | `ALLOWED_HOSTS` missing your domain |
| Form posts return 403 | `CSRF_TRUSTED_ORIGINS` missing/`https://` scheme absent |
| `permission denied for schema public` on migrate | Run the `ALTER DATABASE ... OWNER` from Quickstart step 2 |
| `password authentication failed` | `.env` DB password doesn't exactly match the one set in psql |
| Push: `invalid length` / key errors | See the VAPID "Common mistakes" section |
| Login page crashes with `DoesNotExist` | Social app not attached to the current Site, or duplicate provider apps |
| Changes to `.env`/signals have no effect | Restart the server — both are read at startup |

---

## Project layout (high level)

```
blogs/           Posts, categories, SEO, AI content analysis, link suggestions
notifications/   In-app notifications, push subscriptions, preferences
comments/        Comments, replies, moderation, flags
accounts/        Profiles, auth (allauth), adapters
dashboards/      Publishing & management dashboard
pages/           Static pages (About, Privacy, ...) editable from the dashboard
ads/             Advertisement placements
blogmain/        Project settings and root URLs
templates/       Where all the html files are
```

## License & support

See LICENSE for terms. For setup issues, work through the Troubleshooting
table above first — it covers the failure modes observed in real deployments.