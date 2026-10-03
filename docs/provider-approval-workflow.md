# Provider Approval Workflow

1. A provider registers through `POST /auth/register` with the `provider` role.
2. SkillBridge creates an unpublished provider profile with `Pending` status.
3. The provider updates the profile through `PUT /providers/me`.
4. The provider submits evidence through `POST /providers/me/credentials`.
5. An administrator reviews pending profiles through `GET /admin/providers/pending`.
6. The administrator submits `approve` or `reject` to `POST /admin/providers/{provider_id}/decision`.
7. Approval verifies the submitted credential, changes the provider status to `Approved`, and publishes the profile.
8. Rejection keeps the profile unpublished and changes pending credentials to `Rejected`.

The public provider search returns only published profiles. Any provider profile update returns the profile to pending review and removes it from publication until an administrator approves it again.
