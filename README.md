# Weekview — Minimal Weekly Calendar

A small, production-conscious weekly calendar built for learning Python, Git, CI/CD, Docker, automated testing, and Linux home-server deployment.

Repository: <https://github.com/mohammadrezaheydarinackademin/cicd-pro-calender>

## What it does

- Register and log in with an email address and password.
- See a Monday-to-Sunday weekly calendar.
- Navigate to previous and next weeks, or jump back to the current week.
- Create events by clicking a day.
- Open, edit, and delete events, including past events.
- Create multi-day events.
- Use light mode or dark mode. The theme is stored in the browser.
- Responsive layout for desktop, tablet, and mobile.

Past days and past events are visually faded, but they remain fully clickable and editable.

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3, Flask, SQLAlchemy |
| Frontend | HTML5, CSS3, vanilla JavaScript |
| Database | MariaDB (SQLite is used automatically for local development/tests) |
| Testing | Pytest |
| Containers | Docker, Docker Compose |
| CI | GitHub Actions |

No Node.js backend, React, Vue, Angular, Kubernetes, or external services are used.

## Project structure

```text
.
├── app/
│   ├── __init__.py          # App factory, session loading, CSRF protection
│   ├── models.py            # User and Event models
│   ├── routes.py            # Calendar page, health check, event API
│   ├── auth.py              # Registration, login, logout, auth guards
│   ├── timeutils.py         # UTC storage and Europe/Stockholm conversion
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── calendar.html
│   └── static/
│       ├── css/style.css
│       └── js/
│           ├── calendar.js
│           └── theme.js
├── tests/
│   ├── conftest.py
│   ├── helpers.py
│   ├── test_auth.py
│   ├── test_events.py
│   └── test_calendar.py
├── config.py
├── run.py
├── requirements.txt
├── Dockerfile
├── compose.yaml
├── .dockerignore
├── .gitignore
├── .env.example
├── pytest.ini
├── .github/workflows/ci.yml
├── README.md
└── PROMPT.md
```

## Local development

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create your local environment file

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Edit `.env` and set a strong `SECRET_KEY`. For local development, leave `DATABASE_URL` empty to use SQLite automatically:

```env
SECRET_KEY=replace-with-a-long-random-value
DATABASE_URL=
```

### 4. Run the application

```bash
python run.py
```

Open <http://localhost:5000>.

The SQLite database is created at `instance/calendar.db` on first start.

### Using MariaDB locally

Start a local MariaDB instance, create a database and user, then set:

```env
DATABASE_URL=mysql+pymysql://calendar_user:your_password@127.0.0.1:3306/calendar?charset=utf8mb4
```

Run `python run.py` again. Tables are created automatically if they do not exist.

## Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `SECRET_KEY` | Flask session signing key. Required in production. | Insecure development fallback |
| `DATABASE_URL` | SQLAlchemy database URL. Leave empty for local SQLite. | `sqlite:///calendar.db` |
| `SESSION_COOKIE_SECURE` | Send session cookies only over HTTPS. Set `true` behind HTTPS. | `false` |
| `APP_PORT` | Host port used by Docker Compose. | `5000` |
| `MARIADB_ROOT_PASSWORD` | MariaDB root password used by the container. | none |
| `MARIADB_DATABASE` | MariaDB database name. | none |
| `MARIADB_USER` | MariaDB application user. | none |
| `MARIADB_PASSWORD` | MariaDB application password. | none |
| `DB_INIT_RETRIES` | How many times the app retries table creation at startup. | `10` |
| `DB_INIT_DELAY` | Seconds between database startup retries. | `2` |

Never commit `.env` or real credentials. `.env` is ignored by Git.

## Docker and home-server deployment

### Ports

- Application: `5000` on the host by default (`APP_PORT` changes it).
- MariaDB: `3306` inside the Docker network only. It is **not** published to the host or the internet.

### First-time deployment

```bash
cp .env.example .env
```

Edit `.env` and set at least:

```env
SECRET_KEY=<long-random-value>
MARIADB_ROOT_PASSWORD=<strong-root-password>
MARIADB_DATABASE=calendar
MARIADB_USER=calendar_user
MARIADB_PASSWORD=<strong-app-password>
SESSION_COOKIE_SECURE=false
APP_PORT=5000
```

`DATABASE_URL` can stay empty. Docker Compose builds the MariaDB connection URL from the `MARIADB_*` values.

Build and start:

```bash
docker compose build
docker compose up -d
```

Check status and health:

```bash
docker compose ps
curl http://localhost:5000/health
```

The app waits for MariaDB to become healthy before starting. The application container also has a health check.

### Common commands

| Task | Command |
| --- | --- |
| Build the image | `docker compose build` |
| Start containers | `docker compose up -d` |
| Stop containers | `docker compose down` |
| Restart containers | `docker compose restart` |
| Restart only the app | `docker compose restart calendar-app` |
| View app logs | `docker compose logs -f calendar-app` |
| View database logs | `docker compose logs -f mariadb` |
| View recent logs | `docker compose logs --tail=100 calendar-app` |
| Check container health | `docker compose ps` |
| Check app health | `curl http://localhost:5000/health` |
| Rebuild after changes | `docker compose up -d --build` |

### Data persistence

MariaDB data is stored in the named Docker volume `mariadb_data`.

- `docker compose down` stops the containers but **keeps** the volume and all data.
- `docker compose down -v` deletes the volume and **all calendar data**. Use it only when you intentionally want a clean database.

### Backup and restore

Create a backup:

```bash
docker compose exec mariadb sh -c 'mariadb-dump -u root -p"$MARIADB_ROOT_PASSWORD" "$MARIADB_DATABASE"' > calendar-backup.sql
```

Restore a backup:

```bash
docker compose exec -T mariadb sh -c 'mariadb -u root -p"$MARIADB_ROOT_PASSWORD" "$MARIADB_DATABASE"' < calendar-backup.sql
```

Store backups outside the repository and protect them, because they contain user data.

### Updating the deployment

```bash
git pull
docker compose up -d --build
```

The database volume is preserved during updates.

### HTTPS and secure cookies

For a public home-server deployment, put the app behind an HTTPS reverse proxy (for example Caddy, Nginx, or Traefik) and set:

```env
SESSION_COOKIE_SECURE=true
```

If you use plain HTTP and set this to `true`, the browser will not send the session cookie and login will appear broken.

## Timezone behaviour

- The application timezone is `Europe/Stockholm`.
- Datetimes are stored in UTC as naive `DATETIME` values in MariaDB.
- User input and calendar display are converted to Europe/Stockholm.
- Week boundaries and day grouping respect Europe/Stockholm, including daylight-saving changes.

## Security notes

- Passwords are hashed with Werkzeug's secure password hashing.
- Sessions use signed Flask cookies with `HttpOnly` and `SameSite=Lax`.
- State-changing requests require a CSRF token.
- All event queries are scoped to the logged-in user.
- API queries use SQLAlchemy ORM expressions, not string-concatenated SQL.
- Backend validation checks titles, lengths, dates, times, and date ranges.
- MariaDB is not exposed outside the Docker network.
- Secrets are supplied through environment variables and `.env` is ignored by Git.
- The application container runs as a non-root user.

This is an MVP. For a production system, also consider rate limiting, account lockout, audit logging, database migrations (Alembic), and HTTPS termination at a trusted reverse proxy.

## Automated tests

Run the full test suite from the project root:

```bash
pytest
```

By default, tests use an in-memory SQLite database and never touch production data.

To run the integration tests against MariaDB, provide a separate test database:

```bash
TEST_DATABASE_URL="mysql+pymysql://calendar:calendar@127.0.0.1:3306/calendar_test?charset=utf8mb4" pytest
```

The test database must be separate from the application database. The test fixture drops and recreates its tables.

### Test coverage

- Registration, duplicate email, invalid email, mismatched passwords.
- Login success, incorrect password, logout, unauthorized access.
- CSRF protection.
- Event create, read, update, delete.
- Event ownership and cross-user access prevention.
- Invalid event data and invalid date ranges.
- Past events remaining editable.
- Multi-day events.
- Monday-to-Sunday week boundaries.
- Previous, next, and current week calculation.
- Events appearing in the correct week and only for their owner.

## API overview

All API routes require authentication and use JSON. State-changing requests require the `X-CSRF-Token` header.

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Database-aware health check |
| `GET` | `/api/events` | List the current user's events |
| `POST` | `/api/events` | Create an event |
| `GET` | `/api/events/<id>` | Read one event |
| `PUT` | `/api/events/<id>` | Update one event |
| `DELETE` | `/api/events/<id>` | Delete one event |

Example payload:

```json
{
  "title": "Team meeting",
  "description": "Weekly sync",
  "start_date": "2026-11-10",
  "start_time": "10:00",
  "end_date": "2026-11-10",
  "end_time": "11:00"
}
```

## CI/CD

`.github/workflows/ci.yml` runs on every push and pull request:

1. Starts a MariaDB service container.
2. Sets up Python 3.12.
3. Installs dependencies.
4. Runs the Pytest suite against MariaDB.
5. Reports success or failure.

CI is intentionally separate from deployment. The workflow never connects to the home server and does not deploy automatically.

## Troubleshooting

- **`docker compose` says `.env` is missing:** copy `.env.example` to `.env` and fill in the values.
- **The app restarts or cannot connect to MariaDB:** check `docker compose logs mariadb` and `docker compose ps`. The app retries the database connection during startup.
- **Login loops back to the login page over HTTP:** set `SESSION_COOKIE_SECURE=false` unless you are using HTTPS.
- **Port 5000 is already in use:** change `APP_PORT` in `.env` and restart with `docker compose up -d`.
- **Database password contains special URL characters:** use a URL-safe password (letters, numbers, `-`, `_`) or URL-encode it in `DATABASE_URL`.
- **Need a clean database:** `docker compose down -v` deletes the data volume. Back up first.

## Learning goals

This project is intentionally small but complete: Flask application structure, authentication, ORM modelling, timezone handling, server-side validation, vanilla JS UI, automated tests, Docker Compose, GitHub Actions, and a repeatable home-server deployment.
