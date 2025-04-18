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
