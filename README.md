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

The system rotates active SMTP accounts automatically for outgoing email sends.

## Service Admin dashboard

A dedicated service admin dashboard is available at:

- Frontend route: `/service-admin`
- Backend APIs: `/api/admin/service/*`

Default service-admin credentials (for bootstrap/demo):

- Username: `service-admin`
- Password: set `SERVICE_ADMIN_PASSWORD` explicitly (do not use defaults in production)

> Important: use HTTPS/TLS when calling service-admin endpoints because credentials are passed in request headers.

Override with environment variables on `admin-service`:

- `SERVICE_ADMIN_USERNAME`
- `SERVICE_ADMIN_PASSWORD`
