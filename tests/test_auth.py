import asyncio

from apps.api.app.auth import hash_password, verify_password
from packages.agents.bill_monitoring.workflow import BillMonitoringWorkflow
from packages.shared.config import Settings
from packages.shared.schemas import BillRecord


def test_password_hash_verification_round_trip():
    password_hash = hash_password("correct horse battery staple", Settings())

    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


async def _run_monitoring(topic: str, monitored_topics: set[str]):
    workflow = BillMonitoringWorkflow(
        settings=Settings(congress_api_key=None),
        monitored_topics=monitored_topics,
        email_to="user@example.com",
    )
    bill = BillRecord(
        congress_bill_id="hr-22-119",
        title=f"{topic} bill",
        summary="Voting registration requirements.",
        sponsor="Rep. Example",
        latest_action="Introduced.",
        status="introduced",
        topic=topic,
    )
    return await workflow.determine_relevance({"bill": bill, "topic": topic})


def test_monitoring_relevance_uses_supplied_topics():
    enabled = asyncio.run(_run_monitoring("Elections", {"Elections"}))
    disabled = asyncio.run(_run_monitoring("Elections", {"Agriculture"}))

    assert enabled["relevant"] is True
    assert disabled["relevant"] is False
