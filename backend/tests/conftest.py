import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    # TestClient's context manager triggers the app's lifespan (startup),
    # which is what loads the template/AC registries from YAML.
    with TestClient(create_app()) as test_client:
        yield test_client
