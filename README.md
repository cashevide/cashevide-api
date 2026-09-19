# Cashevide API

The backend for **Cashevide**, a privacy-first platform built for freelancers to make informed decisions about clients while protecting privacy and reducing legal risks. It helps freelancers identify reliable and unreliable clients through structured reviews, and provides tools for managing invoices and freelance business operations.

Built with Django, Django REST Framework, and PostgreSQL.

## Features

- **Structured client reviews.** Instead of public free-form reviews, clients are rated using predefined categories such as paid on time, payment delayed, good communication, professional behavior, unprofessional behavior, and non-payment. This keeps reviews consistent and reduces abuse.
- **Privacy-first client records.** Clients are identified using SHA-256 hashed mobile numbers. Mobile numbers are never stored in plain text, and no sensitive client information is publicly exposed.
- **Invoice management.** Generate professional invoices and manage freelance billing workflows, including PDF generation via WeasyPrint.
- **Freelancer accounts.** JWT-based authentication (via SimpleJWT), plus Google OAuth login.
- **Catalog management.** Manage a catalog of products or services to bill against.
- **Legal document management.** Serve and track acceptance of legal documents (terms, privacy policy, etc.).
- **Webhooks.** Endpoints for handling inbound webhook events, including AWS SNS signature verification.
- **Telegram bot integration.** A dedicated app for Telegram-based interactions.
- **API documentation.** Auto-generated OpenAPI schema and Swagger UI via drf-spectacular, served at the API root.

## Tech Stack

| Purpose               | Library                                                                                                                                                                     |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Web framework         | [Django 6](https://www.djangoproject.com/)                                                                                                                                  |
| API framework         | [Django REST Framework](https://www.django-rest-framework.org/)                                                                                                             |
| Database              | [PostgreSQL](https://www.postgresql.org/)                                                                                                                                   |
| Caching               | [Redis](https://redis.io/) (via django-redis)                                                                                                                               |
| Auth                  | [djangorestframework-simplejwt](https://django-rest-framework-simplejwt.readthedocs.io/), [google-auth](https://google-auth.readthedocs.io/)                                |
| API docs              | [drf-spectacular](https://drf-spectacular.readthedocs.io/) (OpenAPI + Swagger UI)                                                                                           |
| Filtering             | [django-filter](https://django-filter.readthedocs.io/)                                                                                                                      |
| Nested serializers    | [drf-writable-nested](https://github.com/beda-software/drf-writable-nested)                                                                                                 |
| File storage          | [django-storages](https://django-storages.readthedocs.io/) with [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) (Cloudflare R2 / S3-compatible) |
| PDF generation        | [WeasyPrint](https://weasyprint.org/)                                                                                                                                       |
| Image handling        | [Pillow](https://python-pillow.org/), [django-cleanup](https://github.com/un1t/django-cleanup)                                                                              |
| Phone number handling | [phonenumbers](https://github.com/daviddrysdale/python-phonenumbers)                                                                                                        |
| WSGI server           | [Gunicorn](https://gunicorn.org/)                                                                                                                                           |
| Env management        | [python-dotenv](https://github.com/theskumar/python-dotenv), [dj-database-url](https://github.com/jazzband/dj-database-url)                                                 |
| Linting/formatting    | [Ruff](https://docs.astral.sh/ruff/)                                                                                                                                        |
| Type checking         | [django-stubs](https://github.com/typeddjango/django-stubs), [djangorestframework-stubs](https://github.com/typeddjango/djangorestframework-stubs)                          |
| Containerization      | [Docker](https://www.docker.com/), [Nginx](https://nginx.org/)                                                                                                              |

The frontend (web app) is a separate repository built with React, TypeScript, and Vite. See [cashevide-web](https://github.com/cashevide/cashevide-web).

## Project Structure

The codebase follows Django's app-based architecture, with each app owning its own models, views, serializers, and URLs:

```
config/              # Project settings, root URL config, WSGI/ASGI entry points
core/                 # Shared/base models, utilities, and views used across apps
users/                # Freelancer accounts, authentication, permissions
clients/              # Client records (privacy-first, hashed mobile numbers)
catalog/              # Products/services catalog for billing
invoices/             # Invoice models, PDF templates, management commands
reviews/               # Structured client review system
legal/                # Legal document management and acceptance tracking
webhooks/              # Inbound webhook handling (including AWS SNS)
telegram_bot/          # Telegram bot integration
demo/                 # Demo/sandbox app
api_tests/            # HTTP request test files (Kulala) and test scripts
```

Each app follows a consistent internal layout: `models.py`, `serializers.py`, `views.py`, `urls.py`, `admin.py`, `schema.py` (drf-spectacular extensions), `tests.py`, and a `migrations/` folder.

API routes are mounted under `/api/` in `config/urls.py`, for example:

- `/api/users/` (via `users.urls`)
- `/api/` (reviews, clients, catalog, invoices)
- `/api/legal/`
- `/api/telegram/`
- `/api/webhooks/`
- `/api/schema/swagger-ui/` (interactive API docs, also served at the site root)

## Getting Started

### Prerequisites

- Python 3.12 or later
- [uv](https://docs.astral.sh/uv/) for dependency management
- PostgreSQL
- Redis
- Docker and Docker Compose (for containerized setup)

### Quick Setup

```bash
./setup.sh
```

This copies `.env.example` to `.env`, `docker-compose.override.example.yml` to `docker-compose.override.yml`, and `nginx/dev.example.conf` to `nginx/dev.conf`, creating them only if they do not already exist. Fill in the values in `.env` before continuing.

### Running with Docker

```bash
docker compose up
```

This starts the `db` (PostgreSQL), `redis`, and `web` (Django, served via Gunicorn) services.

### Running Locally (without Docker)

```bash
uv sync
uv run manage.py migrate
uv run manage.py runserver
```

Make sure PostgreSQL and Redis are running and reachable using the connection details in your `.env` file.

### Environment Variables

See `.env.example` for the full list of required environment variables, including database credentials, Redis password, Django secret key, admin URL, AWS SES/Cloudflare R2 credentials, and Google OAuth client details.

### Tests

```bash
uv run manage.py test
```

HTTP-level API tests for manual/interactive testing live in `api_tests/kulala/`.

### Linting

```bash
uv run ruff check .
uv run ruff format .
```

## Contributing

Pull requests and external code contributions are not currently accepted. Forking, bug reports, and suggestions via Issues are welcome. See `CONTRIBUTING.md` for details.

## License

Licensed under the O'Saasy License. See `LICENSE.md`.
