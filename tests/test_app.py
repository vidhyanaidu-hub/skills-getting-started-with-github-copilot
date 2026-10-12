from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def activity_store(monkeypatch):
    activities = {
        "Chess Club": {
            "description": "Practice chess",
            "schedule": "Fridays",
            "max_participants": 3,
            "participants": ["existing@example.com"],
        }
    }
    monkeypatch.setattr(app_module, "activities", activities)
    return activities


@pytest.fixture
def client(activity_store):
    return TestClient(app_module.app)


def test_get_activities_returns_activity_data(client, activity_store):
    # Arrange
    expected_activities = activity_store

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, activity_store):
    # Arrange
    activity_name = "Chess Club"
    email = "new@example.com"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert activity_store[activity_name]["participants"] == [
        "existing@example.com",
        email,
    ]


def test_signup_rejects_duplicate_participant(client, activity_store):
    # Arrange
    activity_name = "Chess Club"
    email = "existing@example.com"
    original_participants = activity_store[activity_name]["participants"].copy()

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }
    assert activity_store[activity_name]["participants"] == original_participants


def test_signup_returns_not_found_for_unknown_activity(client, activity_store):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": "new@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_store["Chess Club"]["participants"] == ["existing@example.com"]


def test_unregister_removes_participant(client, activity_store):
    # Arrange
    activity_name = "Chess Club"
    email = "existing@example.com"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert activity_store[activity_name]["participants"] == []


def test_unregister_returns_not_found_for_unknown_activity(client, activity_store):
    # Arrange
    activity_name = "Unknown Club"
    email = "existing@example.com"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_store["Chess Club"]["participants"] == ["existing@example.com"]


def test_unregister_returns_not_found_for_unregistered_participant(client, activity_store):
    # Arrange
    activity_name = "Chess Club"
    email = "missing@example.com"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activity_store[activity_name]["participants"] == ["existing@example.com"]