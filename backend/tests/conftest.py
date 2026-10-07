import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from starlette.testclient import TestClient

import app.database as app_db
from app.database import Base, get_db
from app.main import app

# Shared-cache in-memory SQLite so multiple connections/sessions share tables
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

# Override the app's database engine and session maker
app_db.engine = test_engine
app_db.AsyncSessionLocal = TestingSessionLocal

# Mock Celery delay calls during testing to avoid waiting on an offline Redis broker
from unittest.mock import MagicMock
from app.workers import tasks
_mock_task = MagicMock()
_mock_task.id = "mock-celery-task-id"
tasks.run_workflow.delay = MagicMock(return_value=_mock_task)
tasks.resume_workflow.delay = MagicMock(return_value=_mock_task)
tasks.analyze_repository.delay = MagicMock(return_value=_mock_task)



async def _create_tables():
    async with test_engine.begin() as conn:
        from app.models import user, repository, workflow, agent_run, audit_log, pull_request  # noqa
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    asyncio.run(_create_tables())
    yield
    asyncio.run(_drop_tables())


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
