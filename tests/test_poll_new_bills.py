import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from packages.db.models import Base, BillMonitoring
from packages.jobs.poll_new_bills import poll_new_bills
from packages.shared.schemas import BillRecord


class _FakeCongressClient:
    def __init__(self, bills: list[BillRecord], last_recent_error: str | None = None) -> None:
        self.bills = bills
        self.last_recent_error = last_recent_error

    async def list_recent_bills(self, limit: int = 10, offset: int = 0) -> list[BillRecord]:
        return self.bills[offset : offset + limit]


class _FakeWorkflow:
    async def run(self, bill: BillRecord) -> dict[str, object]:
        return {"topic": bill.topic, "relevant": bill.topic == "Defense"}


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _bill(congress_bill_id: str, topic: str = "Defense") -> BillRecord:
    return BillRecord(
        congress_bill_id=congress_bill_id,
        title="Test Bill",
        summary="Summary",
        sponsor="Sponsor",
        latest_action="Introduced",
        status="introduced",
        topic=topic,
    )


def test_poll_new_bills_reports_provider_warning_when_recent_feed_fails():
    result = asyncio.run(
        poll_new_bills(
            db=_session(),
            congress_client=_FakeCongressClient([], "Congress.gov recent bill feed timed out."),
            workflow=_FakeWorkflow(),
        )
    )

    assert result["fetched"] == 0
    assert result["discovered"] == 0
    assert result["processed"] == 0
    assert result["warning"] == "Congress.gov recent bill feed timed out."


def test_poll_new_bills_counts_already_seen_bills():
    db = _session()
    db.add(BillMonitoring(congress_bill_id="hr-22-119", processed=True, notification_sent=True))
    db.commit()

    result = asyncio.run(
        poll_new_bills(
            db=db,
            congress_client=_FakeCongressClient([_bill("hr-22-119")]),
            workflow=_FakeWorkflow(),
        )
    )

    assert result["fetched"] == 1
    assert result["already_seen"] == 1
    assert result["discovered"] == 0
    assert result["processed"] == 0
    assert result["warning"] is None


def test_poll_new_bills_counts_new_topic_matches():
    result = asyncio.run(
        poll_new_bills(
            db=_session(),
            congress_client=_FakeCongressClient([_bill("hr-8800-119"), _bill("hr-1-119", "Tax & Budget")]),
            workflow=_FakeWorkflow(),
        )
    )

    assert result["fetched"] == 2
    assert result["already_seen"] == 0
    assert result["discovered"] == 2
    assert result["processed"] == 2
    assert result["matched_topics"] == 1
    assert result["notifications"] == 1


def test_poll_new_bills_fetches_past_first_seen_page():
    db = _session()
    for index in range(10):
        db.add(BillMonitoring(congress_bill_id=f"hr-{index}-119", processed=True, notification_sent=False))
    db.commit()

    result = asyncio.run(
        poll_new_bills(
            db=db,
            congress_client=_FakeCongressClient(
                [_bill(f"hr-{index}-119", "Tax & Budget") for index in range(10)] + [_bill("hr-8800-119")]
            ),
            workflow=_FakeWorkflow(),
        )
    )

    assert result["fetched"] == 11
    assert result["already_seen"] == 10
    assert result["discovered"] == 1
    assert result["processed"] == 1
