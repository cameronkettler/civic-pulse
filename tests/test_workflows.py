import asyncio

from packages.agents.bill_lookup import BillLookupWorkflow
from packages.ingestion.congress import CongressClient


def test_bill_lookup_workflow_returns_structured_report():
    async def run_lookup():
        return await BillLookupWorkflow().run("hr-1234-119")

    response = asyncio.run(run_lookup())

    assert response.bill.congress_bill_id == "hr-1234-119"
    assert response.generated_summary
    assert response.generated_analysis
    assert response.stakeholders["possible_supporters"]
    assert response.caveats


def test_congress_client_demo_recent_bills_are_classified():
    async def list_bills():
        return await CongressClient().list_recent_bills(limit=2)

    bills = asyncio.run(list_bills())

    assert len(bills) == 2
    assert all(bill.topic for bill in bills)
