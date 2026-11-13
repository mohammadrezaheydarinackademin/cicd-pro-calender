from datetime import date, timedelta

from flask import (
    Blueprint,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from sqlalchemy import select, text

from . import db
from .auth import login_required
from .models import Event
from .timeutils import (
    parse_local_datetime,
    stockholm_today,
    to_stockholm,
    utcnow,
    week_start_for,
)

main_bp = Blueprint("main", __name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")

MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000

WEEKDAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
WEEKDAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


class ValidationError(Exception):
    def __init__(self, message, fields=None):
        super().__init__(message)
        self.fields = fields or {}


def serialize_event(event: Event) -> dict:
    start_local = to_stockholm(event.start_datetime)
    end_local = to_stockholm(event.end_datetime)
    return {
        "id": event.id,
        "title": event.title,
        "description": event.description or "",
        "start": start_local.replace(tzinfo=None).isoformat(timespec="minutes"),
        "end": end_local.replace(tzinfo=None).isoformat(timespec="minutes"),
        "startDate": start_local.date().isoformat(),
        "endDate": end_local.date().isoformat(),
        "startTime": start_local.strftime("%H:%M"),
        "endTime": end_local.strftime("%H:%M"),
        "isPast": event.end_datetime <= utcnow(),
        "isMultiDay": start_local.date() != end_local.date(),
    }


def _validate_payload(payload: dict):
    title = str(payload.get("title") or "").strip()
    description = str(payload.get("description") or "").strip()
    start_date = str(payload.get("start_date") or "").strip()
    start_time = str(payload.get("start_time") or "").strip()
    end_date = str(payload.get("end_date") or "").strip()
    end_time = str(payload.get("end_time") or "").strip()

    errors = {}
    if not title:
        errors["title"] = "Title is required."
    elif len(title) > MAX_TITLE_LENGTH:
        errors["title"] = f"Title must be at most {MAX_TITLE_LENGTH} characters."
    if len(description) > MAX_DESCRIPTION_LENGTH:
        errors["description"] = (
            f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters."
        )
    if not start_date:
        errors["start_date"] = "Start date is required."
    if not start_time:
        errors["start_time"] = "Start time is required."
    if not end_date:
        errors["end_date"] = "End date is required."
    if not end_time:
        errors["end_time"] = "End time is required."
    if errors:
        raise ValidationError("Please correct the highlighted fields.", errors)

    try:
        start_utc = parse_local_datetime(start_date, start_time)
    except ValueError as exc:
        raise ValidationError("Invalid start date or time.", {"start": str(exc)}) from exc

    try:
        end_utc = parse_local_datetime(end_date, end_time)
    except ValueError as exc:
        raise ValidationError("Invalid end date or time.", {"end": str(exc)}) from exc

    if end_utc <= start_utc:
        raise ValidationError(
            "End date and time must be after the start.",
            {"end": "End must be after start."},
        )

    return title, description, start_utc, end_utc


def _owned_event(event_id: int):
    event = db.session.get(Event, event_id)
    if event is None or event.user_id != g.user.id:
        return None
    return event


def _week_label(week_start: date, week_last: date) -> str:
    start_month = MONTH_NAMES[week_start.month - 1]
    last_month = MONTH_NAMES[week_last.month - 1]
    if week_start.year != week_last.year:
        return (
            f"{week_start.day:02d} {start_month} {week_start.year} – "
            f"{week_last.day:02d} {last_month} {week_last.year}"
        )
    if week_start.month != week_last.month:
        return (
            f"{week_start.day:02d} {start_month} – "
            f"{week_last.day:02d} {last_month} {week_last.year}"
        )
    return f"{week_start.day:02d} – {week_last.day:02d} {last_month} {week_last.year}"


@main_bp.get("/")
def index():
    if getattr(g, "user", None):
        return redirect(url_for("main.calendar"))
    return redirect(url_for("auth.login"))


@main_bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        db.session.rollback()
        return jsonify({"status": "error"}), 503
    return jsonify({"status": "ok"}), 200


@main_bp.get("/calendar")
@login_required
def calendar():
    today = stockholm_today()
    requested = today
    start_param = request.args.get("start")
    if start_param:
        try:
            requested = date.fromisoformat(start_param)
        except ValueError:
            requested = today
        if requested.year < 2 or requested.year > 9998:
            requested = today

    week_start = week_start_for(requested)
    week_end = week_start + timedelta(days=7)
    week_last = week_end - timedelta(days=1)

    week_start_utc = parse_local_datetime(week_start.isoformat(), "00:00")
    week_end_utc = parse_local_datetime(week_end.isoformat(), "00:00")

    events = (
        db.session.execute(
            select(Event)
            .where(
                Event.user_id == g.user.id,
                Event.start_datetime < week_end_utc,
                Event.end_datetime > week_start_utc,
            )
            .order_by(Event.start_datetime.asc(), Event.id.asc())
        )
        .scalars()
        .all()
    )

    days = []
    for offset in range(7):
        day = week_start + timedelta(days=offset)
        days.append(
            {
                "date": day.isoformat(),
                "weekday": WEEKDAY_NAMES[day.weekday()],
                "shortWeekday": WEEKDAY_SHORT[day.weekday()],
                "day": day.day,
                "month": MONTH_NAMES[day.month - 1],
                "isToday": day == today,
                "isPast": day < today,
            }
        )

    data = {
        "weekStart": week_start.isoformat(),
        "weekEnd": week_last.isoformat(),
        "today": today.isoformat(),
        "prevWeek": (week_start - timedelta(days=7)).isoformat(),
        "nextWeek": (week_start + timedelta(days=7)).isoformat(),
        "currentWeek": week_start_for(today).isoformat(),
        "weekLabel": _week_label(week_start, week_last),
        "days": days,
        "events": [serialize_event(event) for event in events],
    }
    return render_template("calendar.html", data=data)


@api_bp.get("/events")
@login_required
def list_events():
    events = (
        db.session.execute(
            select(Event)
            .where(Event.user_id == g.user.id)
            .order_by(Event.start_datetime.asc(), Event.id.asc())
        )
        .scalars()
        .all()
    )
    return jsonify({"events": [serialize_event(event) for event in events]})


@api_bp.post("/events")
@login_required
def create_event():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Send a valid JSON object."}), 400

    try:
        title, description, start_utc, end_utc = _validate_payload(payload)
    except ValidationError as exc:
        return jsonify({"error": str(exc), "fields": exc.fields}), 400

    event = Event(
        user_id=g.user.id,
        title=title,
        description=description or None,
        start_datetime=start_utc,
        end_datetime=end_utc,
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({"event": serialize_event(event)}), 201


@api_bp.get("/events/<int:event_id>")
@login_required
def get_event(event_id: int):
    event = _owned_event(event_id)
    if event is None:
        return jsonify({"error": "Event not found."}), 404
    return jsonify({"event": serialize_event(event)})


@api_bp.put("/events/<int:event_id>")
@login_required
def update_event(event_id: int):
    event = _owned_event(event_id)
    if event is None:
        return jsonify({"error": "Event not found."}), 404

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Send a valid JSON object."}), 400

    try:
        title, description, start_utc, end_utc = _validate_payload(payload)
    except ValidationError as exc:
        return jsonify({"error": str(exc), "fields": exc.fields}), 400

    event.title = title
    event.description = description or None
    event.start_datetime = start_utc
    event.end_datetime = end_utc
    event.updated_at = utcnow()
    db.session.commit()
    return jsonify({"event": serialize_event(event)})


@api_bp.delete("/events/<int:event_id>")
@login_required
def delete_event(event_id: int):
    event = _owned_event(event_id)
    if event is None:
        return jsonify({"error": "Event not found."}), 404

    db.session.delete(event)
    db.session.commit()
    return jsonify({"ok": True})
