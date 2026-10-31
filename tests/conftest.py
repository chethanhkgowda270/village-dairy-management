import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def cow_farmer(client):
    return client.post(
        "/farmers", json={"name": "Ramesh", "village": "Hosahalli", "milk_type": "cow"}
    ).get_json()
