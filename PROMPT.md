# Project Prompt — Minimal Weekly Calendar MVP

## Goal

Build a complete, functional, minimal, and production-conscious weekly calendar application from scratch.

The project is a learning exercise for:

- Python development
- Git and GitHub
- CI/CD
- GitHub Actions
- Automated testing
- Docker and Docker Compose
- Linux server deployment
- Home-server administration

GitHub repository: <https://github.com/mohammadrezaheydarinackademin/cicd-pro-calender>

## Strict project boundary

- Work only inside the current project root.
- Do not create, modify, delete, move, or overwrite files outside the project root.
- Do not use parent-directory paths or follow links outside the project root.
- Do not install global software or change system-wide configuration.
- Do not push, commit, or change remote repositories without explicit permission.
- Never expose credentials, tokens, or passwords.

## Technology stack

Use only:

- Python 3
- Flask
- SQLAlchemy
- HTML5
- CSS3
- Vanilla JavaScript
- MariaDB
- Pytest
- Docker
- Docker Compose
- GitHub Actions

Do not use React, Vue, Angular, a Node.js backend, Kubernetes, unnecessary frameworks, or unnecessary third-party services.

## Application concept

Build a personal weekly calendar.

- Users register and log in with email and password.
- After login, users see a Monday-to-Sunday weekly calendar.
- The calendar displays scheduled events for each day.
- Past days and past events have a faded visual appearance.
- Past events are **not** disabled. Users can open, read, edit, and delete them.
- Future events have a normal appearance.
- The app should feel simple and lightweight, inspired by Google Calendar usability without copying its design.

## Authentication

Implement:

- User registration.
- Login.
- Logout.
- Email and password authentication.
- Secure password hashing.
- Flask session management.
- Protected application routes.

Requirements:

- Each user can access only their own events.
- Users must never view or modify another user's events.
- Validate email addresses.
- Prevent duplicate email registrations.
- No external email service and no email verification for this MVP.

## Weekly calendar

- Display Monday through Sunday.
- Navigate to previous and next weeks.
- Button to return to the current week.
- Highlight today's date.
- Clearly display the current week.
- Display events in their corresponding days.
- Display event start and end times.
- Past days appear faded but remain clickable.
- Support different screen sizes.
- Clicking a day opens the event creation modal with that date selected.

## Event management

Implement complete CRUD:

- Create
- Read
- Update
- Delete

Event fields:

- Title (required)
- Description (optional)
- Start date
- Start time
- End date
- End time

Requirements:

1. Clicking a calendar day opens the creation modal.
2. Automatically populate the selected date.
3. Allow users to enter event information.
4. Save events in MariaDB.
5. Clicking an existing event opens its details.
6. Allow editing existing events.
7. Allow deleting existing events.
8. Ask for confirmation before deleting.
9. Validate all event information on the backend.
10. Prevent an end datetime earlier than the start datetime.
11. Support events spanning multiple days.

## User interface and design

- Modern, clean, minimal interface.
- Light mode and dark mode.
- Responsive desktop and mobile layouts.
- Minimal navigation.
- Clear typography.
- Subtle borders.
- Clean event cards.
- Simple modal forms.
- Good spacing.
- Easy-to-understand buttons.
- Simple visual hierarchy.
- Use CSS and vanilla JavaScript.
- Avoid unnecessary animations and complicated dashboard components.
- Store the theme preference locally in the browser.
- Visually attractive but lightweight.

## Database design

Use MariaDB with SQLAlchemy.

### users

- `id`
- `email`
- `password_hash`
- `created_at`

### events

- `id`
- `user_id`
- `title`
- `description`
- `start_datetime`
- `end_datetime`
- `created_at`
- `updated_at`

Requirements:

- Proper primary keys.
- Foreign key between events and users.
- Appropriate indexes.
- SQLAlchemy relationships.
- Persistent database storage.
- Each event belongs to exactly one user.
- Database data survives container restarts.
- Application timezone: Europe/Stockholm.
- Store datetimes in UTC and convert to Europe/Stockholm for display and user input.

## Security requirements

- Secure password hashing.
- Environment variables for secrets.
- Never hardcode database passwords.
- SQLAlchemy ORM queries.
- No unsafe SQL string concatenation.
- Authentication protection.
- Authorization checks.
- User ownership validation.
- Backend input validation.
- CSRF protection for state-changing requests.
- Secure session cookie settings.
- Proper error handling.
- Do not expose secrets in logs or GitHub.

Create `.env.example` with placeholders:

- `SECRET_KEY=`
- `DATABASE_URL=`
- `MARIADB_ROOT_PASSWORD=`
- `MARIADB_DATABASE=`
- `MARIADB_USER=`
- `MARIADB_PASSWORD=`

Create a proper `.gitignore`. Never commit `.env` or real credentials.

## Project structure

Use a simple structure:

```text
app/
├── __init__.py
├── models.py
├── routes.py
├── auth.py
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   └── calendar.html
└── static/
    ├── css/style.css
    └── js/calendar.js

tests/
├── conftest.py
├── test_auth.py
├── test_events.py
└── test_calendar.py

config.py
run.py
requirements.txt
Dockerfile
compose.yaml
.dockerignore
.gitignore
.env.example
.github/workflows/ci.yml
README.md
PROMPT.md
```

Adjust only when technically necessary. Keep it simple.

## Automated testing

Use Pytest.

### Authentication tests

- User registration.
- Successful login.
- Incorrect password.
- Logout.
- Unauthorized access.
- Duplicate email registration.

### Event tests

- Create event.
- Read event.
- Edit event.
- Delete event.
- Event ownership.
- Prevent accessing another user's events.
- Invalid event data.
- Invalid date and time ranges.
- Multi-day events.

### Calendar tests

- Monday as the first day of the week.
- Sunday as the last day of the week.
- Previous week navigation.
- Next week navigation.
- Current week calculation.
- Events appearing on the correct dates.

### Test database

- Use a separate test database configuration.
- Never run destructive tests against production data.
- Tests must be runnable with `pytest`.
- Tests must be reliable and repeatable.

## GitHub Actions CI

Create `.github/workflows/ci.yml`.

The workflow must:

- Trigger on push.
- Trigger on pull_request.
- Run on `ubuntu-latest`.
- Set up Python.
- Install dependencies.
- Run automated tests.
- Report success or failure.
- Use a MariaDB service container for integration tests.

The CI pipeline must not connect to the home server. Do not implement automatic deployment. Keep CI and CD separate.

## Docker and home-server deployment

Create a `Dockerfile` and `compose.yaml`.

Use two services:

1. `calendar-app`
2. `mariadb`

Requirements:

- Application container.
- MariaDB container.
- Persistent MariaDB volume.
- Environment-based configuration.
- Database health check.
- Application waits for database readiness.
- Restart policies.
- Proper container networking.
- Do not expose MariaDB publicly.
- Do not commit secrets.

The application should be deployable on a Linux home server using Docker Compose.

Document:

- Required ports.
- How to build the image.
- How to start containers.
- How to stop containers.
- How to view logs.
- How to restart containers.
- How to check application health.
- How to preserve database data.
- How to back up and restore the database.
- How to update the deployment safely.
- HTTPS and secure-cookie considerations.
- CI/CD separation and the fact that deployment is manual.
