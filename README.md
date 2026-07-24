# Advanced News & Blog Platform (Django)

A full-featured news/blog platform built with Django 5.2 and PostgreSQL. Includes a
publishing dashboard, category management with dropdown menus, push notifications
(Web Push/VAPID), email newsletters, PWA support, dark mode, SEO tooling
(sitemaps, news sitemap, meta management, content analysis and internal link
suggestions), comments with moderation, an ad-management system, and a responsive
front end.

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

Open psql **as the postgres superuser** — you'll be asked for the password you set
when you installed PostgreSQL:

```bash
psql -U postgres
```

> **Important:** always include `-U postgres`. If you run just `psql`, it defaults to
> your operating-system username and you'll get
> `FATAL: password authentication failed for user "<your-name>"`.
>
> **Windows:** if `psql` is "not recognized", use the full path, e.g.
> `"C:\Program Files\PostgreSQL\18\bin\psql" -U postgres`, or add that `bin`
> folder to your PATH.

At the `postgres=#` prompt, run (choose your own names/password):

```sql
CREATE DATABASE myblog_db;
CREATE USER myblog_user WITH PASSWORD 'choose_a_password';
GRANT ALL PRIVILEGES ON DATABASE myblog_db TO myblog_user;
ALTER DATABASE myblog_db OWNER TO myblog_user;
\q
```

> The `ALTER ... OWNER` line is required on PostgreSQL 15+ — without it,
> migrations fail with "permission denied for schema public".
>
> Password tip: use letters and numbers only. Avoid `@ : / # '` and spaces —
> they can break connection strings.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and **fill in every value**. At minimum you need `SECRET_KEY` and the
`DB_*` variables before the next step, or `migrate` fails with
`settings.DATABASES is improperly configured`.

> **CRITICAL — no spaces in `.env`:** write `KEY=value`, never `KEY= value`.
> A leading or trailing space becomes part of the value and will silently break
> your database password, VAPID key, or email credentials. This is the single
> most common setup mistake.

> **Local development:** set `DEBUG=True` in `.env`. With `DEBUG=False` the app
> forces HTTPS, and the local dev server only speaks HTTP — you'll get a page full
> of `Bad request version` errors. Use `DEBUG=False` only when deploying behind
> real HTTPS.

Generate a fresh `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Migrate, load language data, create your admin user, and run

```bash
python manage.py migrate
python manage.py setup_nltk          # one-time download of language data for content analysis
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000 — the site is running (empty until you add content).

> After any change to `.env` or to signal files, **restart the server**.
> Environment values and signals are read only at startup.

---

## Push Notifications (VAPID keys) — three steps, in order

Web Push requires a VAPID keypair. **You must generate your own.** Follow these
three steps exactly — most push problems come from skipping one.

### Step 1 — generate the keypair

```bash
vapid --gen
```

This writes `private_key.pem` (and `public_key.pem`) to the current folder.

### Step 2 — place the private key

**Move `private_key.pem` into the project root** (the same folder as `manage.py`).
The application loads it from there by path. It is git-ignored and never shipped —
this is why every install generates its own.

### Step 3 — put the public key in `.env`

Print the public key in the format the browser needs:

```bash
vapid --applicationServerKey
```

Copy the output (a base64url string starting with `B`, ~87 characters) into `.env`
— **with no space after the `=`**:

```
VAPID_PUBLIC_KEY=BOr3...your-key...
VAPID_ADMIN_EMAIL=you@yourdomain.com
```

Then **restart the server.**

### Testing push

- Test in a **normal browser window (Chrome/Edge/Firefox), NOT incognito** —
  incognito blocks notifications and service workers, so subscriptions silently
  fail.
- Load the site, **allow notifications** when prompted (this creates the subscription).
- Verify a subscription was recorded before publishing:
  ```bash
  python manage.py shell -c "from notifications.models import PushSubscription; print(PushSubscription.objects.count())"
  ```
  If this is `0`, the browser never subscribed — check the browser console
  (F12) for a service-worker or key error.
- Then publish a post — the notification should arrive (browser and, on supported
  devices, phone).

### Common VAPID mistakes (these WILL break push)

1. **Space in `.env`** — `VAPID_PUBLIC_KEY= B...` breaks the key. Remove the space.
2. **Private key not in the project root** — must sit next to `manage.py`.
3. **Public key doesn't match the private key** — both must come from the same
   `vapid --gen` run. Regenerate both together if unsure.
4. **Testing in incognito** — use a normal window.

If push fails with `Could not deserialize key data ... invalid length`, the
private key file is malformed or in the wrong place — regenerate and re-place it.
A `410 Gone` in the logs is normal — an expired browser subscription, which the
app deactivates automatically.

---

## Email (newsletter + notifications)

Email uses the **console backend by default** — until you configure SMTP, "sent"
emails are printed to the server console (a safe default; nothing crashes). To
send real mail, set these in `.env`:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=your16charapppassword
DEFAULT_FROM_EMAIL=you@gmail.com
```

For Gmail:

1. Enable **2-Step Verification** on the account (required before App Passwords appear).
2. Google Account → Security → **App passwords** → create one.
3. Enter the 16-character password in `.env` **without spaces**.

Real sending is independent of `DEBUG`, so you can test it locally. Confirm with:

```bash
python manage.py shell -c "from django.core.mail import send_mail; print(send_mail('Test','It works',None,['you@gmail.com']))"
```

A return of `1` with **no message printed to the console** means SMTP sent it (check
your inbox / spam). If the whole message prints to the console instead, you're still
on the console backend — set `EMAIL_BACKEND` above.

---

## First-run configuration

1. **Site identity** — log into the dashboard → Site Settings; set your site name,
   tagline, and social links. Also set `SITE_NAME` and `SITE_URL` in `.env`
   (used by the PWA manifest and system emails).
2. **Logo** — replace the placeholder in `static/images/` with your own; run
   `python manage.py collectstatic` if serving collected statics.
3. **Categories** — create categories in the dashboard. Give a category a **Parent**
   to build navbar dropdowns ("Name ▾" with children); categories without children
   render as plain links.
4. **First post** — create a post and set status to **Published**. Only Published
   posts appear on the site; publishing is what triggers subscriber notifications.
   Notifications fire only on the *transition* to Published, so re-saving an
   already-published post does not re-notify.
5. **Ads (optional)** — the ad system ships with standard positions. Create them once
   with `python manage.py setup_ad_positions`, then add ads in admin and assign each
   to a position. Ad slots are already placed in the templates (in-content, sidebar,
   footer, etc.).
6. **Social login (optional)** — Google/Facebook login is supported but **off until
   configured**. The signup/login pages work without it (social buttons simply don't
   appear). To enable, create the provider apps in Django admin → Social applications,
   attach each to your Site, and supply your own OAuth credentials from the provider.
   `SITE_ID` in settings must match a row in the Sites table; use exactly one app per
   provider per site.

### How the home page fills in

Sections show content as it becomes available: mark a post **Featured** for the
featured slot; mark posts **Editor's Pick** for that sidebar; category blocks need
2+ posts for their sidebars. With fewer than ~6 posts some sections show empty-state
messages — this is expected and resolves as you publish.

---

## Deploying to production

1. In `.env`:
   ```
   DEBUG=False
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
   SITE_URL=https://yourdomain.com
   ```
   `CSRF_TRUSTED_ORIGINS` requires the scheme (`https://`); `ALLOWED_HOSTS` must not
   include it.
2. `python manage.py collectstatic` (WhiteNoise serves statics).
3. Run behind a production server (gunicorn/uwsgi + nginx). **HTTPS is required** for
   push and PWA install. With `DEBUG=False` the app redirects to HTTPS and trusts
   `X-Forwarded-Proto` — ensure your reverse proxy sets that header, or you'll get a
   redirect loop.
4. Update the Sites entry (admin → Sites) to your real domain and confirm `SITE_ID`
   points at it — social login and absolute URLs depend on this.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `FATAL: password authentication failed for user "<your name>"` opening psql | Ran `psql` without `-U postgres` — it used your OS username. Use `psql -U postgres`. |
| `settings.DATABASES is improperly configured` on migrate | `DB_*` values in `.env` are empty — fill them. |
| `permission denied for schema public` on migrate | Run the `ALTER DATABASE ... OWNER` from step 2. |
| `password authentication failed` for the DB | `.env` DB password doesn't exactly match psql — check for a stray space. |
| Console floods with `Bad request version` / "accessing over HTTPS" | `DEBUG=False` enabled the SSL redirect; set `DEBUG=True` locally and retest in a **private window** (the redirect is cached). |
| Browser forces `https://` on localhost / `ERR_SSL_PROTOCOL_ERROR`, but `curl` returns 200 | Cached HSTS. Clear at `chrome://net-internals/#hsts` (delete `127.0.0.1`), fully restart the browser, or test in a private window. |
| Push does nothing; `PushSubscription` count is 0 | Browser never subscribed — test in a **normal window** (not incognito), allow notifications, check the console for service-worker/key errors. |
| Push: `invalid length` / key errors | Private key missing from project root, or a space in `VAPID_PUBLIC_KEY`. See the VAPID section. |
| `vapid --gen` → `curve must be an EllipticCurve instance` | `cryptography` too new for `py-vapid`; the pinned version in `requirements.txt` fixes this. |
| Emails print to the console instead of sending | Console backend (the default). Set `EMAIL_BACKEND` to SMTP in `.env`. |
| Signup/login page 500s with `DoesNotExist` in `get_app` | A social provider button is rendering with no configured app — ensure the templates guard social login (this build does) and that any enabled provider has an app attached to the current Site. |
| Changes to `.env`/signals have no effect | Restart the server — both are read at startup. |

---

## Project layout (high level)

```
blogs/           Posts, categories, SEO, content analysis, link suggestions
notifications/   In-app notifications, push subscriptions, preferences
comments/        Comments, replies, moderation, flags
accounts/        Profiles, auth (allauth), adapters
dashboards/      Publishing & management dashboard
pages/           Static pages (About, Privacy, ...) editable from the dashboard
ads/             Advertisement positions and placements
blogmain/        Project settings and root URLs
```

## License & support

See LICENSE for terms. For setup issues, work through the Troubleshooting table
above first — it covers the failure modes observed in real clean-install testing.