from uuid import UUID, uuid4

from pydantic import HttpUrl
from sqlmodel import Session

from app.api.v1.models import Website


def test_create_website_success(
    client, test_db: Session, user_with_notification_preference
):
    user, _ = user_with_notification_preference

    payload = {
        "user_id": str(user.id),
        "name": "Example",
        "url": "https://example.com/",
    }
    response = client.post("/websites/", json=payload)
    assert response.status_code == 201

    # Use Pydantic to normalize the input like the API
    normalized_url = str(HttpUrl(payload["url"]))
    assert response.json()["url"] == normalized_url

    # Verify DB state
    data = response.json()
    website_in_db = test_db.get(
        Website, UUID(data["id"])
    )  # Convert json str id back to UUID
    assert website_in_db is not None
    assert website_in_db.name == "Example"
    assert str(website_in_db.url) == "https://example.com/"


def test_create_website_already_exists(
    client, test_db: Session, user_with_notification_preference
):
    user, _ = user_with_notification_preference
    normalized_url = str(HttpUrl("https://example.com"))
    existing_website = Website(
        id=uuid4(), name="Existing Website", url=normalized_url, user=user
    )
    test_db.add(existing_website)
    test_db.commit()

    payload = {
        "user_id": str(user.id),
        "name": existing_website.name,
        "url": existing_website.url,
    }
    response = client.post("/websites/", json=payload)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_all_websites(client, test_db: Session, user_with_notification_preference):
    user, _ = user_with_notification_preference
    website1 = Website(
        id=uuid4(), name="Website 1", url="https://example.com/", user=user
    )
    website2 = Website(
        id=uuid4(), name="Website 2", url="https://example.org/", user=user
    )
    website3 = Website(
        id=uuid4(), name="Website 3", url="https://example.net/", user=user
    )
    test_db.add_all([website1, website2, website3])
    test_db.commit()
    test_db.refresh(website1)
    test_db.refresh(website2)
    test_db.refresh(website3)

    # Test first page
    response = client.get("/websites/?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["has_next"] is True

    # Test next page
    assert data["next_cursor"]
    response = client.get(f"/websites/?limit=2&cursor={data['next_cursor']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1


def test_get_single_website(
    client, test_db: Session, user_with_notification_preference
):
    user, _ = user_with_notification_preference
    website = Website(
        id=uuid4(), name="Test Website", url="https://example.com/", user=user
    )
    test_db.add(website)
    test_db.commit()
    test_db.refresh(website)

    response = client.get(f"/websites/{website.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(website.id)


def test_update_website(client, test_db: Session, user_with_notification_preference):
    user, _ = user_with_notification_preference
    normalized_url = HttpUrl("https://example.com")
    website = Website(
        id=uuid4(), name="Test Website", url=str(normalized_url), user=user
    )
    test_db.add(website)
    test_db.commit()
    test_db.refresh(website)

    normalised_updated_url = HttpUrl("https://updated.com")

    payload = {
        "name": "Updated Website",
        "url": str(normalised_updated_url),
        "is_active": False,
    }
    response = client.patch(f"/websites/{website.id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Website"
    assert data["url"] == str(normalised_updated_url)
    assert data["is_active"] is False


def test_update_non_existent_website(client):
    non_existent_id = uuid4()
    normalised_updated_url = HttpUrl("https://updated.com")
    payload = {
        "name": "Updated Website",
        "url": str(normalised_updated_url),
        "is_active": False,
    }
    response = client.patch(f"/websites/{non_existent_id}", json=payload)
    assert response.status_code == 404
    assert f"Website with id {non_existent_id} not found" in response.json()["detail"]


def test_delete_website(client, test_db: Session, user_with_notification_preference):
    user, _ = user_with_notification_preference
    normalized_url = HttpUrl("https://example.com")
    website = Website(
        id=uuid4(), name="Test Website", url=str(normalized_url), user=user
    )
    test_db.add(website)
    test_db.commit()
    test_db.refresh(website)

    response = client.delete(f"/websites/{website.id}")
    assert response.status_code == 204
    assert response.content == b""  # No content expected for 204 No Content

    # Verify the website has been deleted from the database
    deleted_website = test_db.get(Website, website.id)
    assert deleted_website is None


def test_delete_non_existent_website(client):
    non_existent_id = uuid4()

    response = client.delete(f"/websites/{non_existent_id}")
    assert response.status_code == 404
    assert f"Website with id {non_existent_id} not found" in response.json()["detail"]


def test_get_all_uptime_logs_success(client, test_uptime_logs):
    website_id = test_uptime_logs[0].website_id
    response = client.get(f"/websites/{website_id}/uptime-logs")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == len(test_uptime_logs)
    assert data["has_next"] is False


def test_get_uptime_logs_filtered_is_up_true(client, test_uptime_logs):
    website_id = test_uptime_logs[0].website_id
    response = client.get(f"/websites/{website_id}/uptime-logs?is_up=true")
    assert response.status_code == 200
    logs = response.json()["data"]
    assert len(logs) == 2
    assert all(log["is_up"] is True for log in logs)


def test_get_uptime_logs_filtered_is_up_false(client, test_uptime_logs):
    website_id = test_uptime_logs[0].website_id
    response = client.get(f"/websites/{website_id}/uptime-logs?is_up=false")
    assert response.status_code == 200
    logs = response.json()["data"]
    assert len(logs) == 1
    assert all(log["is_up"] is False for log in logs)


def test_get_uptime_logs_with_limit(client, test_uptime_logs):
    website_id = test_uptime_logs[0].website_id
    response = client.get(f"/websites/{website_id}/uptime-logs?limit=2")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs["data"]) == 2
    assert logs["has_next"] is True


def test_get_uptime_logs_after_timestamp(client, test_uptime_logs):
    # Pick the timestamp of the first log
    after_timestamp = test_uptime_logs[0].timestamp.isoformat()
    website_id = test_uptime_logs[0].website_id
    response = client.get(f"/websites/{website_id}/uptime-logs?after={after_timestamp}")
    assert response.status_code == 200
    logs = response.json()["data"]
    assert len(logs) == 2
    assert all(log["timestamp"] > after_timestamp for log in logs)


def test_get_logs_for_non_existent_website(client):
    non_existent_uuid = uuid4()
    response = client.get(f"/websites/{non_existent_uuid}/uptime-logs")
    assert response.status_code == 404
    assert response.json()["detail"] == "Website not found"


def test_search_website_success(
    client, test_db: Session, user_with_notification_preference
):
    user, _ = user_with_notification_preference
    website1 = Website(
        id=uuid4(), name="Test Website 1", url="https://example.com/", user=user
    )
    website2 = Website(
        id=uuid4(), name="Test Website 2", url="https://example.org/", user=user
    )
    test_db.add_all([website1, website2])
    test_db.commit()

    response = client.get("/websites/search?q=Test")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["has_next"] is False


def test_search_website_paginated(
    client, test_db: Session, user_with_notification_preference
):
    user, _ = user_with_notification_preference
    website1 = Website(
        id=uuid4(), name="Test Website 1", url="https://example.com/", user=user
    )
    website2 = Website(
        id=uuid4(), name="Test Website 2", url="https://example.org/", user=user
    )
    website3 = Website(
        id=uuid4(), name="Test Website 3", url="https://example.net/", user=user
    )
    test_db.add_all([website1, website2, website3])
    test_db.commit()

    response = client.get("/websites/search?q=Test&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["has_next"] is True
    assert data["next_cursor"] == str(website2.id)
