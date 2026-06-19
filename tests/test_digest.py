from packages.jobs.digest_generation import build_daily_digest
from packages.shared.schemas import MonitoringBill


def test_build_daily_digest_lists_bills():
    digest = build_daily_digest(
        [
            MonitoringBill(
                congress_bill_id="s-42-119",
                title="Privacy Protection Act",
                topic="Privacy",
                summary="Adds privacy safeguards.",
            )
        ]
    )

    assert "s-42-119" in digest
    assert "Privacy Protection Act" in digest
