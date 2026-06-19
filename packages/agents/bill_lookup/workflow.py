from typing import Any, TypedDict

from packages.ingestion.congress import CongressClient
from packages.ingestion.fec import FECClient
from packages.ingestion.lobbying import LobbyingDisclosureClient
from packages.shared.schemas import BillLookupResponse, BillRecord

try:
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover - exercised only when optional dependency is absent
    END = "__end__"
    StateGraph = None


class BillLookupState(TypedDict, total=False):
    bill_id: str
    bill: BillRecord
    sponsor: dict[str, Any]
    finance: dict[str, Any]
    lobbying: dict[str, Any]
    generated_summary: str
    generated_analysis: str
    stakeholders: dict[str, list[str]]
    caveats: list[str]
    confidence: str


class BillLookupWorkflow:
    def __init__(
        self,
        congress_client: CongressClient | None = None,
        fec_client: FECClient | None = None,
        lobbying_client: LobbyingDisclosureClient | None = None,
    ) -> None:
        self.congress = congress_client or CongressClient()
        self.fec = fec_client or FECClient()
        self.lobbying = lobbying_client or LobbyingDisclosureClient()
        self.graph = self._build_graph()

    async def run(self, bill_id: str) -> BillLookupResponse:
        initial: BillLookupState = {"bill_id": bill_id}
        if self.graph is None:
            state = await self._run_fallback(initial)
        else:
            state = await self.graph.ainvoke(initial)
        return BillLookupResponse(**state)

    def _build_graph(self):
        if StateGraph is None:
            return None

        workflow = StateGraph(BillLookupState)
        workflow.add_node("retrieve_bill", self.retrieve_bill)
        workflow.add_node("retrieve_sponsor", self.retrieve_sponsor)
        workflow.add_node("retrieve_finance", self.retrieve_finance)
        workflow.add_node("retrieve_lobbying", self.retrieve_lobbying)
        workflow.add_node("aggregate_findings", self.aggregate_findings)
        workflow.add_node("generate_report", self.generate_report)

        workflow.set_entry_point("retrieve_bill")
        workflow.add_edge("retrieve_bill", "retrieve_sponsor")
        workflow.add_edge("retrieve_sponsor", "retrieve_finance")
        workflow.add_edge("retrieve_finance", "retrieve_lobbying")
        workflow.add_edge("retrieve_lobbying", "aggregate_findings")
        workflow.add_edge("aggregate_findings", "generate_report")
        workflow.add_edge("generate_report", END)
        return workflow.compile()

    async def _run_fallback(self, state: BillLookupState) -> BillLookupState:
        for step in (
            self.retrieve_bill,
            self.retrieve_sponsor,
            self.retrieve_finance,
            self.retrieve_lobbying,
            self.aggregate_findings,
            self.generate_report,
        ):
            state.update(await step(state))
        return state

    async def retrieve_bill(self, state: BillLookupState) -> BillLookupState:
        return {"bill": await self.congress.get_bill(state["bill_id"])}

    async def retrieve_sponsor(self, state: BillLookupState) -> BillLookupState:
        return {"sponsor": await self.congress.get_sponsor(state["bill"].sponsor)}

    async def retrieve_finance(self, state: BillLookupState) -> BillLookupState:
        return {"finance": await self.fec.get_candidate_finance_patterns(state["bill"].sponsor)}

    async def retrieve_lobbying(self, state: BillLookupState) -> BillLookupState:
        return {"lobbying": await self.lobbying.search_activity(state["bill"].title)}

    async def aggregate_findings(self, state: BillLookupState) -> BillLookupState:
        lobbying_clients = [
            item.get("client_name", "Unknown stakeholder")
            for item in state.get("lobbying", {}).get("registrations", [])
        ]
        return {
            "stakeholders": {
                "possible_supporters": lobbying_clients[:1] or ["Agency modernization advocates"],
                "possible_opponents": lobbying_clients[1:] or ["Civil liberties watchdogs"],
            },
            "caveats": [
                "Provider data can lag official filings and should be verified before publication.",
                "Stakeholder posture is inferred from disclosed activity and bill subject matter.",
            ],
            "confidence": self._confidence(state),
        }

    async def generate_report(self, state: BillLookupState) -> BillLookupState:
        bill = state["bill"]
        supporters = ", ".join(state["stakeholders"]["possible_supporters"])
        opponents = ", ".join(state["stakeholders"]["possible_opponents"])
        summary = f"{bill.congress_bill_id}: {bill.title}. {bill.summary}"
        analysis = (
            f"{bill.sponsor} introduced the bill, which is currently {bill.status}. "
            f"The latest action is: {bill.latest_action} Possible supporters include {supporters}. "
            f"Possible opposition or scrutiny may come from {opponents}. Campaign finance signals "
            "should be treated as contextual patterns rather than proof of influence."
        )
        return {"generated_summary": summary, "generated_analysis": analysis}

    def _confidence(self, state: BillLookupState) -> str:
        confidences = {
            state.get("finance", {}).get("confidence", "low"),
            state.get("lobbying", {}).get("confidence", "low"),
        }
        return "medium" if "medium" in confidences else "low"
