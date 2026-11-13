import os
import time

from sqlalchemy.exc import OperationalError

from app import create_app, db

app = create_app()

if not os.environ.get("SECRET_KEY"):
    app.logger.warning(
        "SECRET_KEY is not set; using an insecure development fallback."
    )


def init_db() -> None:
    retries = int(app.config.get("DB_INIT_RETRIES", 10))
    delay = float(app.config.get("DB_INIT_DELAY", 2))
    last_error = None
    os.makedirs(app.instance_path, exist_ok=True)

    for attempt in range(1, retries + 1):
        try:
            with app.app_context():
                db.create_all()
            return
        except OperationalError as exc:
            last_error = exc
            app.logger.warning(
                "Database not ready (attempt %s/%s): %s", attempt, retries, exc
            )
            time.sleep(delay)

    if last_error is not None:
        raise last_error


init_db()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )
