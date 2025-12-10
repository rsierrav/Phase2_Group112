from fastapi.testclient import TestClient

from backend.backend.app.main import app
from backend.backend.app.dependencies import get_dynamodb_table


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, Item):
        self.items[Item["id"]] = Item
        return {}

    def get_item(self, Key):
        item = self.items.get(Key["id"])
        return {"Item": item} if item is not None else {}

    def scan(self, **kwargs):
        return {"Items": list(self.items.values())}


def test_upload_list_retrieve_roundtrip():
    # one shared FakeTable for this test
    table = FakeTable()

    async def override_table():
        return table

    # Override the real DynamoDB dependency with our fake one
    app.dependency_overrides[get_dynamodb_table] = override_table
    client = TestClient(app)

    # 1. Upload
    resp = client.post(
        "/artifact/model",
        headers={"X-Authorization": "bearer test"},
        json={"url": "https://huggingface.co/google-bert/bert-base-uncased"},
    )
    assert resp.status_code == 201
    uploaded = resp.json()
    art_id = uploaded["metadata"]["id"]

    # 2. List
    resp_list = client.post(
        "/artifacts",
        headers={"X-Authorization": "bearer test"},
        json=[{"name": "*"}],
    )
    assert resp_list.status_code == 200
    listed = resp_list.json()
    assert len(listed) == 1
    assert listed[0]["id"] == art_id

    # 3. Retrieve
    resp_get = client.get(
        f"/artifacts/model/{art_id}",
        headers={"X-Authorization": "bearer test"},
    )
    assert resp_get.status_code == 200
    retrieved = resp_get.json()
    assert retrieved["metadata"]["id"] == art_id
    assert retrieved["data"]["url"].endswith("bert-base-uncased")

    # Clean up overrides
    app.dependency_overrides.clear()
