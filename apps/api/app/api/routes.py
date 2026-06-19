import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from packages.agents.bill_lookup import BillLookupWorkflow
from packages.agents.bill_lookup.input_resolver import BillInputResolutionError
from packages.agents.bill_monitoring import BillMonitoringWorkflow
from packages.db import get_session
from packages.db.models import Bill, BillMonitoring, GeneratedReport, UserInterest
from packages.ingestion.congress import CongressClient
from packages.jobs.poll_new_bills import poll_new_bills
from packages.shared.schemas import BillLookupRequest, BillLookupResponse, MonitoringBill

router = APIRouter()


class InterestUpdate(BaseModel):
    enabled: bool


@router.post("/bills/lookup", response_model=BillLookupResponse)
async def lookup_bill(payload: BillLookupRequest, db: Session = Depends(get_session)):
    try:
        response = await BillLookupWorkflow().run(payload.bill_id)
    except BillInputResolutionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Congress.gov did not find that bill number. Check the bill type, number, and Congress.",
            ) from exc
        raise
    bill = upsert_bill(db, response)
    db.add(
        GeneratedReport(
            bill_id=bill.id,
            generated_summary=response.generated_summary,
            generated_analysis=response.generated_analysis,
        )
    )
    db.commit()
    return response


@router.get("/monitoring/recent", response_model=list[MonitoringBill])
async def recent_bills(db: Session = Depends(get_session)):
    rows = db.query(Bill).order_by(Bill.created_at.desc()).limit(25).all()
    if rows:
        return [
            MonitoringBill(
                congress_bill_id=row.congress_bill_id,
                title=row.title,
                topic=row.topic,
                summary=row.summary,
                introduced_date=row.introduced_date,
                alert_status="sent",
            )
            for row in rows
        ]

    demo = await CongressClient().list_recent_bills(limit=5)
    return [
        MonitoringBill(
            congress_bill_id=bill.congress_bill_id,
            title=bill.title,
            topic=bill.topic,
            summary=bill.summary,
            introduced_date=bill.introduced_date,
            alert_status="demo",
        )
        for bill in demo
    ]


@router.post("/monitoring/poll")
async def poll_monitoring(db: Session = Depends(get_session)):
    result = await poll_new_bills(db=db, workflow=BillMonitoringWorkflow())
    return result


@router.get("/interests")
def list_interests(db: Session = Depends(get_session)):
    return db.query(UserInterest).order_by(UserInterest.topic.asc()).all()


@router.patch("/interests/{topic}")
def update_interest(topic: str, payload: InterestUpdate, db: Session = Depends(get_session)):
    interest = db.query(UserInterest).filter(UserInterest.topic == topic).one_or_none()
    if interest is None:
        interest = UserInterest(topic=topic, enabled=payload.enabled)
        db.add(interest)
    else:
        interest.enabled = payload.enabled
    db.commit()
    db.refresh(interest)
    return interest


def upsert_bill(db: Session, response: BillLookupResponse) -> Bill:
    record = response.bill
    bill = db.query(Bill).filter(Bill.congress_bill_id == record.congress_bill_id).one_or_none()
    if bill is None:
        bill = Bill(congress_bill_id=record.congress_bill_id)
        db.add(bill)

    bill.title = record.title
    bill.summary = record.summary
    bill.sponsor = record.sponsor
    bill.introduced_date = record.introduced_date
    bill.latest_action = record.latest_action
    bill.status = record.status
    bill.topic = record.topic
    db.flush()
    return bill
