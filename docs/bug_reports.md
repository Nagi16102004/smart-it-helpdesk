# Bug Reports — Smart IT Help Desk

## BUG-01

| Field | Details |
|---|---|
| Bug ID | BUG-01 |
| Title | Agent can resolve a ticket directly from "Assigned" status without passing through "In Progress" |
| Module | Ticket Status Workflow (resolve_ticket route) |
| Severity | Medium |
| Priority | High |
| Environment | Local dev, Flask debug server, Chrome/Edge browser |
| Precondition | A ticket exists with status = "Assigned" and is assigned to the logged-in agent |
| Steps to Reproduce | 1. Login as the assigned agent 2. Directly navigate to /resolve-ticket/<ticket_id> for a ticket still in "Assigned" status (without clicking "Start Progress" first) |
| Expected Result | The system should block this and show an error like "Ticket must be In Progress before it can be resolved," redirecting back to the agent's ticket list |
| Actual Result (before fix) | The Resolve Ticket form loaded normally and allowed the agent to mark the ticket as Resolved directly from "Assigned" status |
| Fix Applied | Added a status check (`if ticket.status != 'In Progress'`) at the start of the resolve_ticket route in app.py, before rendering the form or processing the POST request |
| Retest Result | Visiting /resolve-ticket/<id> for an Assigned ticket now shows "Ticket must be In Progress before it can be resolved." and redirects to the agent ticket list, as expected |
| Status | Fixed and Verified |