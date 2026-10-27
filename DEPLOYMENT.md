# EduNext SL — running and hosting

Django serves both the API (`/api/v1/`) and the built React app, so the browser talks to a single
origin (cookies and CORS just work). Layout: `backend/` (Django) and `EduNextSL Frontend/`
(React/Vite; builds into `backend/frontend_dist/`).

External services: **Neon** (PostgreSQL), **Cloudinary** (photos, videos, documents),
**Brevo** (transactional email), **Google** (sign-in), **Render** (hosting).

## 1. Configuration (`backend/.env`, never committed)

All variables are listed with placeholders in `backend/.env.example`. Key points:

| Service | Variables | Notes |
|---|---|---|
| Neon | `DATABASE_URL`, `DIRECT_DATABASE_URL` | `DATABASE_URL` must be the **pooled** string (host contains `-pooler`); the app uses it at runtime. `DIRECT_DATABASE_URL` is the direct string, used only for migrations (`build.sh`). The code detects `-pooler` and turns off server-side cursors / prepared statements for PgBouncer. |
| Cloudinary | `CLOUDINARY_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | Enables the signed-upload endpoint and makes Cloudinary Django's default file storage. |
| Brevo | `BREVO_API_KEY`, `EMAIL_FROM_ADDRESS`, `EMAIL_FROM_NAME` | `BREVO_API_KEY` must be an **API key** (starts `xkeysib-`, Brevo → SMTP & API → API Keys). An SMTP key (`xsmtpsib-`) is rejected in production unless `BREVO_SMTP_LOGIN` is also set, and SMTP is blocked on Render's free tier. `EMAIL_FROM_ADDRESS` must be a verified sender in Brevo. |
| Google | `GOOGLE_OAUTH_CLIENT_ID` | Web OAuth client ID; authorize your site URLs as JavaScript origins. No secret needed. |
| Site | `FRONTEND_BASE_URL`, `DJANGO_ADMIN_URL`, `LEGAL_*_VERSION` | `FRONTEND_BASE_URL` is the public site URL (used in email links). |

Tests never read `.env` and never contact real services.

## 2. Local development

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py migrate          # uses the pooled URL; schema changes are fine locally
python manage.py runserver        # http://localhost:8000
```

Frontend with hot reload (proxies `/api` to Django): `cd "EduNextSL Frontend"; npm run dev` → http://localhost:5173.
Single-origin like production: `npm run build` (writes `backend/frontend_dist`), then open http://localhost:8000.

Without `BREVO_API_KEY`, development prints emails to the console.

## 3. Hosting on Render

`render.yaml` (repo root) defines one web service. No database is created: Neon is external.

1. Push the repo to GitHub → Render → **New → Blueprint** → pick the repo.
2. Fill in every `sync: false` variable in the dashboard (copy values from `backend/.env`):
   `DATABASE_URL` (pooled), `DIRECT_DATABASE_URL`, `CLOUDINARY_*`, `BREVO_API_KEY`, `EMAIL_FROM_*`,
   `GOOGLE_OAUTH_CLIENT_ID`, `DJANGO_ADMIN_URL`, `LEGAL_*_VERSION`, and `FRONTEND_BASE_URL`
   (= the service URL, e.g. `https://edunext-sl.onrender.com`).
3. After the first deploy add that URL to the Google OAuth authorized JavaScript origins.
4. Create an admin: `python manage.py createsuperuser` (Render shell, or locally: Neon is shared).

Each deploy runs `backend/build.sh`: install deps, build React, `collectstatic`, `migrate` and
`createcachetable` over the direct Neon connection. Runtime: gunicorn (2 workers × 4 threads), settings
`config.settings.production` (HTTPS redirect, HSTS, secure cookies, Swagger off). Render's health check
is `/api/v1/health/` (checks the database).

Rate limiting uses a database cache (`CACHE_URL=dbcache://django_cache`) so counters are shared by all workers.

## 4. Uploads (Cloudinary)

Browsers upload straight to Cloudinary (large videos never pass through the web server):

1. `POST /api/v1/media/signature/` (logged in) with `{"resource_type": "image" | "video" | "raw"}`.
2. POST multipart form data to the returned `upload_url`: the `file`, `api_key`, `signature` and every
   entry of `form_fields`, unchanged. The Cloudinary response has `secure_url` and `public_id`.

Uploads are confined to `edunext/users/<user id>/<type>` and to allowed file types (signed, so the client
cannot change them). Size limits (`max_bytes`: image 10 MB, video 200 MB, documents 25 MB) are enforced by
the client; for server-enforced limits create a Cloudinary upload preset. Server-side code can save files with
Django's `default_storage` (Cloudinary-backed).

## 5. Emails

Welcome emails (student/company variants) and password-reset emails are sent through Brevo with the EduNext SL
logo (Cloudinary asset `edunext/brand/logo`), a call-to-action button and a plain-text alternative. They are sent
on a background thread, so a provider outage never slows or fails a request (failures are logged, never raised).

## 6. Google and Facebook sign-in

A first social sign-in creates a **student** account after the user accepts the terms; returning users just sign
in. If the email already belongs to a password account (or to the other provider) the API answers
`409 ACCOUNT_EXISTS` (no auto-linking, because registration does not verify email ownership). If Facebook shares no
email the API answers `400 SOCIAL_EMAIL_REQUIRED`.

**Facebook setup (one time)**
1. https://developers.facebook.com → My Apps → **Create App** → use case *Authenticate and request data from users
   with Facebook Login* → app type *Consumer*.
2. Add the **Facebook Login** product → Settings: enable *Login with the JavaScript SDK* and add your site
   (`https://edunextsl.onrender.com`, plus `http://localhost:8000`/`http://localhost:5173` for development) to
   *Allowed Domains for the JavaScript SDK*.
3. App Settings → Basic: copy **App ID** and **App Secret** into `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET`
   (locally in `backend/.env`, on Render in the dashboard). Add a *Privacy Policy URL* and a contact email there too.
4. While the app is in **Development mode** only people added under App Roles (admins/developers/testers) can sign in.
   To open it to everyone, switch the app to **Live**. The `email` and `public_profile` permissions work without
   App Review for basic Facebook Login.

The browser sends Facebook's access token; the backend verifies it with Facebook (it must be issued to your app and
belong to the profile it reads) using the App Secret, which never leaves the server.

## 7. Known limits

- Free Render web services sleep when idle; the first request after a sleep is slow (plus a cold Neon connection).
- Email threads are daemon threads: a deploy/restart in the middle of a send can drop that one email.
- Facebook sign-in is not implemented.
