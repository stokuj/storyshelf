#test_routes_find_pairs.py

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_route_returns_200():
    """Test that the /find-pairs/ route returns a 200 status code when given valid input."""

    response = client.post("/find-pairs/", json=
        {
            "content": "Bilbo met Gandalf near the Shire. Gandalf spoke with Thorin. Bilbo and Thorin argued about the treasure. Only Gandalf remained calm.",
            "names": ["Bilbo", "Gandalf", "Thorin"]
        }
    )
    data = response.json()

    assert response.status_code == 200
    assert "pairs" in data
    assert isinstance(data["pairs"], list)  #check if pairs is a list
    assert len(data["pairs"]) > 0           #check if pairs is not empty


def test_route_missing_content_returns_422():
    """Test that the /find-pairs/ route returns a 422 status code when the content field is missing."""

    response = client.post("/find-pairs/", json=
        {
            "names": ["Bilbo", "Gandalf", "Thorin"]
        }
    )
    assert response.status_code == 422
    detail = response.json()["detail"][0]
    assert detail["type"] == "missing"
    assert "content" in detail["loc"]


def test_route_missing_names_returns_422():
    """Test that the /find-pairs/ route returns a 422 status code when the names field is missing."""

    response = client.post("/find-pairs/", json=
        {
            "content": "Bilbo met Gandalf near the Shire. Gandalf spoke with Thorin. Bilbo and Thorin argued about the treasure. Only Gandalf remained calm."
        }
    )
    assert response.status_code == 422
    detail = response.json()["detail"][0]
    assert detail["type"] == "missing"
    assert "names" in detail["loc"]

