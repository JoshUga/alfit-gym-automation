# alfit-gym-automation
Alfit is a microservices-based platform enabling gyms to register, manage members, and automate communication via EvolutionAPI. It features AI-powered auto-responses using configurable large language models, scheduled notifications, and comprehensive analytics. The architecture emphasizes independent, scalable microservices orchestrated via Docker 

## SMTP / EmailEngine setup

SMTP sending is managed through the `email-service` using EmailEngine account mappings.

- Configure EmailEngine access in `docker-compose.yml` under `email-service` environment:
  - `EMAILENGINE_BASE_URL` (example: `http://emailengine:3000`)
  - `EMAILENGINE_API_TOKEN`
- Add one or more SMTP/EmailEngine accounts via API:
  - `POST /api/email/smtp/accounts`
- Run account checks:
  - `POST /api/email/smtp/health-check`

### Optional EmailEngine auto-init (no manual account setup)

The email-service can auto-bootstrap one SMTP account at startup from environment variables:

- `EMAILENGINE_AUTO_INIT=true` (default)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- Optional: `SMTP_GYM_ID`, `SMTP_ACCOUNT_NAME`, `SMTP_FROM_EMAIL`, `SMTP_FROM_NAME`, `SMTP_SECURE`, `EMAILENGINE_INIT_ACCOUNT_ID`

When `EMAILENGINE_API_TOKEN` is not provided, the service now generates a deterministic runtime token from SMTP bootstrap env vars.

The system rotates active SMTP accounts automatically for outgoing email sends.

## Service Admin dashboard

A dedicated service admin dashboard is available at:

- Standalone admin-service UI: `/admin/service/dashboard` (served by admin-service)
- Backend APIs: `/api/v1/admin/service/*`

Additional service-admin data operations:

- Purge managed data (keep backups by default): `POST /api/v1/admin/service/data/purge`
- Restore backup snapshot: `POST /api/v1/admin/service/backups/{backup_id}/restore`

Default service-admin credentials (for bootstrap/demo):

- Username: `service-admin`
- Password: set `SERVICE_ADMIN_PASSWORD` explicitly (do not use defaults in production)

> Important: use HTTPS/TLS when calling service-admin endpoints because credentials are passed in request headers.

Override with environment variables on `admin-service`:

- `SERVICE_ADMIN_USERNAME`
- `SERVICE_ADMIN_PASSWORD`
