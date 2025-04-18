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
    import pdb

    pdb.set_trace()
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
        id=uuid4(), name="Existing Website", url=str(normalized_url), user=user
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
