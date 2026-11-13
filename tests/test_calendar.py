from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from tests import helpers


def test_week_runs_monday_to_sunday(client):
    helpers.register(client)

    data = helpers.calendar_data(client, start="2026-11-11")

    assert data["weekStart"] == "2026-11-09"
    assert data["weekEnd"] == "2026-11-15"
    assert [day["weekday"] for day in data["days"]] == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    assert data["days"][0]["date"] == "2026-11-09"
    assert data["days"][-1]["date"] == "2026-11-15"


def test_previous_and_next_week_navigation(client):
    helpers.register(client)
    data = helpers.calendar_data(client, start="2026-11-11")

    assert data["prevWeek"] == "2026-11-02"
    assert data["nextWeek"] == "2026-11-16"

    previous = helpers.calendar_data(client, start=data["prevWeek"])
    assert previous["weekStart"] == "2026-11-02"

    following = helpers.calendar_data(client, start=data["nextWeek"])
    assert following["weekStart"] == "2026-11-16"


def test_current_week_is_based_on_stockholm_today(client):
    helpers.register(client)
    data = helpers.calendar_data(client)

    today = datetime.now(ZoneInfo("Europe/Stockholm")).date()
    expected = (today - timedelta(days=today.weekday())).isoformat()

    assert data["weekStart"] == expected
    assert data["currentWeek"] == expected
    assert any(day["isToday"] for day in data["days"])


def test_events_are_returned_for_the_correct_week(client):
    helpers.register(client)
    helpers.create_event(
        client,
        title="Wednesday meeting",
        start_date="2026-11-11",
        start_time="10:00",
        end_date="2026-11-11",
        end_time="11:00",
    )
    helpers.create_event(
        client,
        title="Next week meeting",
        start_date="2026-11-18",
        start_time="10:00",
        end_date="2026-11-18",
        end_time="11:00",
    )

    data = helpers.calendar_data(client, start="2026-11-09")
    titles = [event["title"] for event in data["events"]]

    assert "Wednesday meeting" in titles
    assert "Next week meeting" not in titles
    meeting = next(
        event for event in data["events"] if event["title"] == "Wednesday meeting"
    )
    assert meeting["startDate"] == "2026-11-11"


def test_multi_day_event_appears_in_every_overlapping_week(client):
    helpers.register(client)
    helpers.create_event(
        client,
        title="Long conference",
        start_date="2026-11-09",
        start_time="09:00",
        end_date="2026-11-16",
        end_time="17:00",
    )

    first_week = helpers.calendar_data(client, start="2026-11-09")
    second_week = helpers.calendar_data(client, start="2026-11-16")
    before = helpers.calendar_data(client, start="2026-11-02")

    assert [event["title"] for event in first_week["events"]] == ["Long conference"]
    assert [event["title"] for event in second_week["events"]] == ["Long conference"]
    assert before["events"] == []


def test_past_and_future_days_are_flagged(client):
    helpers.register(client)

    past = helpers.calendar_data(client, start="2020-01-06")
    future = helpers.calendar_data(client, start="2099-01-05")

    assert all(day["isPast"] for day in past["days"])
    assert not any(day["isPast"] for day in future["days"])


def test_calendar_shows_only_the_logged_in_users_events(client):
    helpers.register(client, email="one@example.com")
    helpers.create_event(
        client,
        title="Private event",
        start_date="2026-11-11",
        start_time="10:00",
        end_date="2026-11-11",
        end_time="11:00",
    )
    helpers.logout(client)
    helpers.register(client, email="two@example.com")

    data = helpers.calendar_data(client, start="2026-11-09")

    assert data["events"] == []
