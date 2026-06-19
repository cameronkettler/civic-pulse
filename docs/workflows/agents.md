# Agent Workflow Documentation

## Bill Lookup Agent

Input: `bill_id`

Steps:

1. Retrieve bill data from Congress.gov.
2. Retrieve sponsor data.
3. Retrieve finance data from OpenFEC.
4. Retrieve lobbying data.
5. Aggregate findings into supporter and opposition hypotheses.
6. Generate a human-readable report and structured response.

Output: `BillLookupResponse`, including bill metadata, generated summary, generated analysis, stakeholders, caveats, and confidence.

## Bill Monitoring Agent

Input: newly discovered `BillRecord`

Steps:

1. Retrieve or accept the bill record.
2. Classify topic using keyword rules that can be replaced by an LLM classifier.
3. Summarize the bill.
4. Determine relevance against enabled monitoring topics.
5. Generate email content.
6. Queue the notification.

Output: notification payload and summary state.

## Design Notes

Both workflows use LangGraph when available and include a sequential fallback to keep tests and demo environments resilient. The workflow classes are independent from FastAPI and can be moved into workers later.
