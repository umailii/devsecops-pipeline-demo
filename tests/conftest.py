import pytest

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.db"))
    return app.test_client()
