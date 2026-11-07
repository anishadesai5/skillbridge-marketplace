# Milestone submission, revision, and simulated release

This increment implements project-plan Tasks 17, 18.1, and 18.2.

## Workflow

1. The assigned provider submits a deliverable URL and optional notes for a Pending milestone.
2. The booking customer can approve the submission or request a revision with a required reason.
3. A revision changes the milestone to `RevisionReq`; the provider can resubmit and the submission counter increases.
4. Approval changes the milestone to `Approved` and records one simulated `MilestoneRelease` ledger transaction.

## Reconciliation and duplicate protection

The simulated release amount equals `booking total × milestone allocation percentage`. The prototype applies a 10% commission and stores the provider payout as `release amount − commission`. The database constraint verifies that the amounts reconcile. A unique constraint on milestone and transaction type prevents duplicate releases, while the approval service returns the existing transaction when the same approval is submitted again.

No real payment credentials, processor calls, or money transfers are used.
