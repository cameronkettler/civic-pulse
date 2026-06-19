import logging

from packages.shared.config import Settings, get_settings
from packages.shared.schemas import NotificationPayload

logger = logging.getLogger(__name__)


class EmailNotificationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.outbox: list[NotificationPayload] = []

    async def queue(self, payload: NotificationPayload) -> None:
        self.outbox.append(payload)
        logger.info("queued notification", extra={"bill_id": payload.bill_id, "topic": payload.topic})

    async def send_digest(self, payloads: list[NotificationPayload]) -> dict[str, int | str]:
        if not payloads:
            return {"status": "skipped", "sent": 0}
        self.outbox.extend(payloads)
        return {"status": "queued", "sent": len(payloads)}
