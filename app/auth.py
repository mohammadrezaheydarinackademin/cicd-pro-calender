import re
import secrets
from functools import wraps
from urllib.parse import unquote, urlparse

from flask import (
    Blueprint,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from . import db
from .models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


def is_valid_email(email: str) -> bool:
    return bool(email) and len(email) <= 255 and bool(EMAIL_RE.match(email))


def is_safe_redirect(target: str) -> bool:
    if not target:
        return False
    decoded = unquote(target)
    if any(ord(character) < 32 for character in decoded):
        return False
    parsed = urlparse(decoded)
    return (
        not parsed.scheme
        and not parsed.netloc
        and decoded.startswith("/")
        and not decoded.startswith("//")
        and "\\" not in decoded
    )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if getattr(g, "user", None) is None:
            if request.blueprint == "api" or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required."}), 401
            next_path = request.full_path if request.query_string else request.path
            return redirect(url_for("auth.login", next=next_path))
        return view(*args, **kwargs)

    return wrapped


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if getattr(g, "user", None):
        return redirect(url_for("main.calendar"))

    email = ""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""
        errors = []

        if not is_valid_email(email):
            errors.append("Enter a valid email address.")
        if len(password) < MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if not errors:
            existing = db.session.execute(
                select(User).where(User.email == email)
            ).scalar_one_or_none()
            if existing:
                errors.append("An account with this email already exists.")
            else:
                user = User(email=email)
                user.set_password(password)
                db.session.add(user)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    errors.append("An account with this email already exists.")
                else:
                    session.clear()
                    session["user_id"] = user.id
                    session["csrf_token"] = secrets.token_urlsafe(32)
                    session.permanent = True
                    flash("Welcome! Your account has been created.", "success")
                    return redirect(url_for("main.calendar"))

        for message in errors:
            flash(message, "error")

    return render_template("register.html", email=email)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if getattr(g, "user", None):
        return redirect(url_for("main.calendar"))

    email = ""
    next_path = request.args.get("next", "")
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        next_path = request.form.get("next") or next_path
        user = db.session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            session["csrf_token"] = secrets.token_urlsafe(32)
            session.permanent = True
            flash("Welcome back!", "success")
            if is_safe_redirect(next_path):
                return redirect(next_path)
            return redirect(url_for("main.calendar"))

        flash("Invalid email or password.", "error")

    return render_template("login.html", email=email, next_path=next_path)


@auth_bp.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
