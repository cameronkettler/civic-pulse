from packages.shared.schemas import MonitoringBill


def build_daily_digest(bills: list[MonitoringBill]) -> str:
    if not bills:
        return "No new monitored bills matched your interests today."

    lines = ["Civic Pulse daily digest", ""]
    for bill in bills:
        lines.append(f"- {bill.congress_bill_id} | {bill.topic} | {bill.title}")
    return "\n".join(lines)
