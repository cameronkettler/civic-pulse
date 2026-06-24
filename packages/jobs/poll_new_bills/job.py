from sqlalchemy.orm import Session

from packages.agents.bill_monitoring import BillMonitoringWorkflow
from packages.db.models import Bill, BillMonitoring
from packages.ingestion.congress import CongressClient
from packages.shared.config import get_settings
from packages.shared.schemas import BillRecord


async def poll_new_bills(
    db: Session,
    workflow: BillMonitoringWorkflow | None = None,
    congress_client: CongressClient | None = None,
    monitored_topics: set[str] | None = None,
    email_to: str | None = None,
) -> dict[str, int | str | None]:
    settings = get_settings()
    congress = congress_client or CongressClient(settings)
    monitor = workflow or BillMonitoringWorkflow(
        congress_client=congress,
        settings=settings,
        monitored_topics=monitored_topics,
        email_to=email_to,
    )
    page_limit = max(1, settings.monitoring_poll_limit)
    max_fetch = max(page_limit, settings.monitoring_poll_max_fetch)
    candidates: list[BillRecord] = []
    offset = 0
    warning: str | None = None

    while offset < max_fetch:
        limit = min(page_limit, max_fetch - offset)
        page = await congress.list_recent_bills(limit=limit, offset=offset)
        warning = getattr(congress, "last_recent_error", None)
        candidates.extend(page)
        if warning or len(page) < limit:
            break
        offset += limit

    fetched = len(candidates)
    already_seen = 0
    discovered = 0
    processed = 0
    matched_topics = 0
    notifications = 0
    seen_candidate_ids: set[str] = set()

    if fetched == 0 and warning is None:
        warning = "Congress.gov returned no recent bills for this poll window."

    for candidate in candidates:
        if candidate.congress_bill_id in seen_candidate_ids:
            continue
        seen_candidate_ids.add(candidate.congress_bill_id)

        existing = (
            db.query(BillMonitoring)
            .filter(BillMonitoring.congress_bill_id == candidate.congress_bill_id)
            .one_or_none()
        )
        if existing is not None:
            already_seen += 1
            continue

        discovered += 1
        state = await monitor.run(candidate)
        notification_sent = bool(state.get("relevant"))
        matched_topics += int(notification_sent)
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
    return {
        "fetched": fetched,
        "already_seen": already_seen,
        "discovered": discovered,
        "processed": processed,
        "matched_topics": matched_topics,
        "notifications": notifications,
        "warning": warning,
    }
