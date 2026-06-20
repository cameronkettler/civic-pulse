from sqlalchemy.orm import Session

from packages.agents.bill_monitoring import BillMonitoringWorkflow
from packages.db.models import Bill, BillMonitoring
from packages.ingestion.congress import CongressClient
from packages.shared.config import get_settings


async def poll_new_bills(
    db: Session,
    workflow: BillMonitoringWorkflow | None = None,
    congress_client: CongressClient | None = None,
    monitored_topics: set[str] | None = None,
    email_to: str | None = None,
) -> dict[str, int]:
    settings = get_settings()
    congress = congress_client or CongressClient(settings)
    monitor = workflow or BillMonitoringWorkflow(
        congress_client=congress,
        settings=settings,
        monitored_topics=monitored_topics,
        email_to=email_to,
    )
    candidates = await congress.list_recent_bills(limit=settings.monitoring_poll_limit)

    discovered = 0
    processed = 0
    notifications = 0

    for candidate in candidates:
        existing = (
            db.query(BillMonitoring)
            .filter(BillMonitoring.congress_bill_id == candidate.congress_bill_id)
            .one_or_none()
        )
        if existing is not None:
            continue

        discovered += 1
        state = await monitor.run(candidate)
        notification_sent = bool(state.get("relevant"))
        notifications += int(notification_sent)

        db.add(
            BillMonitoring(
                congress_bill_id=candidate.congress_bill_id,
                processed=True,
                notification_sent=notification_sent,
            )
        )
        bill = db.query(Bill).filter(Bill.congress_bill_id == candidate.congress_bill_id).one_or_none()
        if bill is None:
            bill = Bill(congress_bill_id=candidate.congress_bill_id)
            db.add(bill)
        bill.title = candidate.title
        bill.summary = candidate.summary
        bill.sponsor = candidate.sponsor
        bill.introduced_date = candidate.introduced_date
        bill.latest_action = candidate.latest_action
        bill.status = candidate.status
        bill.topic = state.get("topic", candidate.topic)
        processed += 1

    db.commit()
    return {"discovered": discovered, "processed": processed, "notifications": notifications}
