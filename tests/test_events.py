from sqlalchemy import select

from app import db
from app.models import Event
from tests import helpers


def test_create_read_update_delete_event(client):
    helpers.register(client)

    created = helpers.create_event(client)
    assert created.status_code == 201
    body = created.get_json()["event"]
    event_id = body["id"]
    assert body["title"] == "Team meeting"
    assert body["startDate"] == "2026-11-10"
    assert body["startTime"] == "10:00"
    assert body["endTime"] == "11:00"

    read = client.get(f"/api/events/{event_id}")
    assert read.status_code == 200
    assert read.get_json()["event"]["description"] == "Weekly sync"

    updated = client.put(
        f"/api/events/{event_id}",
        json={
            "title": "Updated meeting",
            "description": "",
            "start_date": "2026-11-10",
            "start_time": "12:00",
            "end_date": "2026-11-10",
            "end_time": "13:30",
        },
        headers=helpers.api_headers(client),
    )
    assert updated.status_code == 200
    updated_body = updated.get_json()["event"]
    assert updated_body["title"] == "Updated meeting"
    assert updated_body["startTime"] == "12:00"
    assert updated_body["endTime"] == "13:30"

    deleted = client.delete(
        f"/api/events/{event_id}", headers=helpers.api_headers(client)
    )
    assert deleted.status_code == 200
    assert client.get(f"/api/events/{event_id}").status_code == 404


def test_event_ownership_is_enforced(client, app):
    helpers.register(client, email="owner@example.com")
    created = helpers.create_event(client, title="Owner event")
    event_id = created.get_json()["event"]["id"]

    helpers.logout(client)
    helpers.register(client, email="other@example.com")

    assert client.get(f"/api/events/{event_id}").status_code == 404
    assert (
        client.put(
            f"/api/events/{event_id}",
            json={
                "title": "Hijacked",
                "start_date": "2026-11-10",
                "start_time": "10:00",
                "end_date": "2026-11-10",
                "end_time": "11:00",
            },
            headers=helpers.api_headers(client),
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/events/{event_id}", headers=helpers.api_headers(client)
        ).status_code
        == 404
    )

    listed = client.get("/api/events")
    assert listed.status_code == 200
    assert listed.get_json()["events"] == []

    with app.app_context():
        stored = db.session.execute(
            select(Event).where(Event.id == event_id)
        ).scalar_one()
        assert stored.title == "Owner event"


def test_invalid_event_data_is_rejected(client):
    helpers.register(client)

    missing_title = helpers.create_event(client, title="   ")
    assert missing_title.status_code == 400
    assert "title" in missing_title.get_json()["fields"]

    backwards = helpers.create_event(
        client,
        start_date="2026-11-10",
        start_time="12:00",
        end_date="2026-11-10",
        end_time="11:00",
    )
    assert backwards.status_code == 400
    assert "after the start" in backwards.get_json()["error"]

    invalid_date = helpers.create_event(client, start_date="not-a-date")
    assert invalid_date.status_code == 400

    not_json = client.post(
        "/api/events",
        data="this is not json",
        content_type="text/plain",
        headers=helpers.api_headers(client),
    )
    assert not_json.status_code == 400


def test_multi_day_event_is_stored_and_serialized(client):
    helpers.register(client)

    response = helpers.create_event(
        client,
        title="Conference",
        start_date="2026-11-09",
        start_time="09:00",
        end_date="2026-11-11",
        end_time="17:00",
    )

    assert response.status_code == 201
    event = response.get_json()["event"]
    assert event["isMultiDay"] is True
    assert event["startDate"] == "2026-11-09"
    assert event["endDate"] == "2026-11-11"


def test_past_events_remain_editable_and_deletable(client):
    helpers.register(client)

    past = helpers.create_event(
        client,
        title="Past event",
        start_date="2020-01-06",
        start_time="09:00",
        end_date="2020-01-06",
        end_time="10:00",
    )
    assert past.status_code == 201
    past_event = past.get_json()["event"]
    event_id = past_event["id"]
    assert past_event["isPast"] is True

    updated = client.put(
        f"/api/events/{event_id}",
        json={
            "title": "Past event edited",
            "start_date": "2020-01-06",
            "start_time": "09:00",
            "end_date": "2020-01-06",
            "end_time": "11:00",
        },
        headers=helpers.api_headers(client),
    )
    assert updated.status_code == 200
    assert updated.get_json()["event"]["title"] == "Past event edited"

    deleted = client.delete(
        f"/api/events/{event_id}", headers=helpers.api_headers(client)
    )
    assert deleted.status_code == 200
    assert client.get(f"/api/events/{event_id}").status_code == 404
