import asyncio
from contextlib import contextmanager

from src.web.routes import registration


class _FakeCrud:
    def __init__(self):
        self.created_tasks = []

    def create_registration_task(self, db, task_uuid, proxy=None, email_service_id=None):
        self.created_tasks.append(
            {
                "task_uuid": task_uuid,
                "proxy": proxy,
                "email_service_id": email_service_id,
            }
        )


@contextmanager
def _fake_db_context():
    yield object()


def test_run_outlook_batch_registration_forwards_registration_type(monkeypatch):
    fake_crud = _FakeCrud()
    forwarded = {}

    async def fake_run_batch_registration(**kwargs):
        forwarded.update(kwargs)

    monkeypatch.setattr(registration, "crud", fake_crud)
    monkeypatch.setattr(registration, "get_db", _fake_db_context)
    monkeypatch.setattr(registration, "run_batch_registration", fake_run_batch_registration)

    asyncio.run(
        registration.run_outlook_batch_registration(
            batch_id="batch-1",
            service_ids=[101, 202],
            skip_registered=True,
            proxy="http://proxy.local:8080",
            interval_min=5,
            interval_max=15,
            concurrency=2,
            mode="pipeline",
            registration_type="parent",
        )
    )

    assert len(fake_crud.created_tasks) == 2
    assert [item["email_service_id"] for item in fake_crud.created_tasks] == [101, 202]
    assert forwarded["email_service_type"] == "outlook"
    assert forwarded["email_service_id"] is None
    assert forwarded["registration_type"] == "parent"
