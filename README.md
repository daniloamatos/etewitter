# Etewitter

Etewitter is a Django application for publishing short posts, following accounts, and having conversations through replies and direct messages. It includes a chronological home timeline, profile pages, search, mentions, notifications, saved posts, reposts, and browser-based end-to-end encrypted messaging. The interface supports Brazilian Portuguese and US English.

**Live site:** [etewitter.wearedang.co](https://etewitter.wearedang.co). The application is hosted on an AWS EC2 instance. Cloudflare manages DNS and routes proxied domain traffic to the instance; Nginx on EC2 terminates HTTPS and forwards HTTP and WebSocket requests to the Django ASGI application running in Docker. The Cloudflare Worker setup below is a separate deployment option.

## How the application works

After signing in, a user’s home timeline combines original posts from accounts they follow with their own posts. Reposts are timeline events: they are ordered by the time of the repost, independently of when the original post was published. Users can open a post to read its reply thread; reply previews expand inline up to two levels, while selecting a post opens its detail page.

Users can publish posts and replies, attach images, mention other accounts, like or repost content, save posts, and follow or unfollow accounts. While composing, mention suggestions help select followed accounts. A mention creates a notification for the mentioned user. Profile previews expose account details and follow actions from the surrounding interface. Search covers accounts and post content, and notifications are shown newest first.

Direct conversations use an authenticated WebSocket connection for live delivery. The browser encrypts message text and image data before sending them to the server. The server stores and relays ciphertext; each browser keeps its user’s private key in IndexedDB and publishes only the corresponding public key.

## Technical overview

- **Django application:** Separate apps handle registration, authentication, profiles, search, posts, notifications, and chat. Django’s custom `Usuario` model uses UUID identifiers and case-insensitive username lookup.
- **Relational content model:** Posts, replies, likes, mentions, follows, repost events, saved items, reports, and notifications are represented as database records and relationships. Database constraints prevent duplicate follow/repost/save relationships and enforce single-target records for saved items and reports.
- **Timeline ordering:** Original posts and reposts are assembled as timeline events and sorted by their respective publication or repost timestamps.
- **ASGI and Channels:** Django HTTP routes and authenticated WebSocket routes are served through the ASGI application. WebSocket origins are checked against allowed hosts. The configured channel layer is in-memory, suitable for local single-process development; a multi-worker deployment needs a shared Channels layer such as Redis.
- **Browser cryptography:** The client creates P-256 ECDH keys and uses AES-GCM to encrypt message payloads. Private keys remain in browser IndexedDB. The server stores one public key per account, so using the account in a different browser creates and publishes a new key that replaces the previous public key. There is no key synchronization, server-side private-key recovery, or multi-device key management; the old browser's private key is needed to decrypt messages encrypted for it. The demo seeder does not create messages because it cannot provision browser-held private keys.
- **Uploads:** Image uploads are checked for supported formats and size limits, decoded with Pillow, and normalized before storage. Animated images are retained as animations.
- **Localization and interface:** Django localization supports `pt-br` and `en-us`; the selected locale is handled through Django’s language middleware. The interface also includes dark and light themes and client-side interactions for mentions, profile previews, reply expansion, and unread-message indicators.
- **Development storage:** SQLite is the default database. Uploaded media is stored under `uploads/`; collected static assets go to `staticfiles/`.

## Run locally

Python 3.12 or newer is recommended. From the repository root:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. `seed_demo` creates 50 sample accounts (25 Portuguese and 25 English), with posts, replies, likes, reposts, follows, and notifications. The command is intended for local development and refuses to run when `DJANGO_DEBUG=False`. It can be run again to restore the sample accounts and content.

All sample accounts use the password `EteDemo2026!`. Example usernames:

- Portuguese: `marina`, `caio`, `luiza`, `rafaelcodes`, `thiagofront`
- English: `alexmorgan`, `jamietaylor`, `emilychen`, `oliverreed`, `gracelee`

To reset the local database and reload examples:

```sh
python manage.py flush
python manage.py migrate
python manage.py seed_demo
```

For encrypted messaging, sign in to two demo accounts in separate browser profiles and start a conversation. Keep each account in the same browser profile: signing that account in from another browser publishes a different public key and replaces the key currently registered for that account.

## Configuration and deployment

The Django settings read configuration from environment variables. `.env.example` documents the available values, but Django does not load `.env` files automatically. Set these values in the process environment for a deployment:

```text
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<a long, random secret>
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
```

When debug is disabled, the application requires `DJANGO_SECRET_KEY` and enables HTTPS redirects, secure session and CSRF cookies, and HSTS. Configure HTTPS at the proxy or web server and provide the correct host list. SMTP settings are optional; the default email backend writes messages to the console.

Apply database migrations and collect static assets during deployment:

```sh
python manage.py migrate
python manage.py collectstatic
```

Run the ASGI application with an ASGI-capable server for WebSocket support. Replace the in-memory channel layer with a shared backend before running multiple workers. The default database is SQLite, so select and configure a production database explicitly if the deployment requires concurrent write capacity or horizontal scaling. User uploads are stored separately from static assets and need persistent storage and appropriate serving rules.

The app uses Django 5.2 LTS and Channels 4 for maintained framework and WebSocket support. Keep these dependencies updated to their latest patch releases.

## Checks

```sh
python manage.py check
python manage.py test
```

## Deploy to Cloudflare Workers

The Cloudflare configuration runs Django in a Linux Container behind a Worker. This keeps the existing Django, Channels, and image-processing dependencies in their normal Python environment. It requires Cloudflare Containers to be enabled for the account and a Docker-compatible build environment.

In **Workers Builds**, use the repository root as the root directory, leave **Build command** empty, and set **Deploy command** to `npx wrangler deploy`. Disable preview builds for this Worker: Cloudflare Worker Previews do not support Workers that use Durable Objects/Containers. Configure a separate staging Worker if you need a preview environment.

Set `DJANGO_ALLOWED_HOSTS` to the public Worker hostname (and any custom domains) in the Worker's environment. Add `DJANGO_SECRET_KEY` as a Worker secret; do not put it in `wrangler.jsonc` or commit it. The container starts with `DJANGO_DEBUG=False`, runs migrations, and serves the ASGI app through Daphne.

The current Django settings use a local SQLite database and local upload directory. Container disk is ephemeral, so this starter configuration is suitable for bringing the app up for evaluation, but user data and uploaded files need persistent storage before treating it as a production deployment. The Worker is limited to one container instance because the configured SQLite database and in-memory Channels layer are not shared across instances.

## Deploy to AWS EC2

For a traditional VM deployment that keeps Django, Channels, SQLite, and uploads together, see [`deploy/aws/README.md`](deploy/aws/README.md). It uses Docker Compose, persistent instance storage, and Nginx for HTTPS and WebSocket proxying.
