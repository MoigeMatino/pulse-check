# PulseCheck - Uptime Monitoring and SSL Management System

🚧 **UNDER DEVELOPMENT** 🚧

PulseCheck is a modern, all-in-one tool for monitoring website uptime and SSL certificate health. It provides real-time notifications via email, SMS, and Slack, ensuring you’re always aware of downtime, SSL expirations, or critical issues—so you can respond quickly and keep your services running smoothly.

## Objective
PulseCheck aims to help businesses and individuals maintain their online presence by:
- Minimizing downtime with proactive alerts.
- Tracking SSL certificate expirations and notifying users in advance.
- Offering a centralized API and (planned) dashboard for managing website status and alerts.

## Features
1. **Uptime Monitoring** (In Progress):
   - Periodically checks website availability.
2. **SSL Monitoring**:
   - Validates SSL certificates using socket-based checks.
   - Logs results with pagination and filtering by validity status.
3. **Real-Time Alerts** (Planned):
   - Sends notifications via SMS, email, and Slack for detected issues.
4. **Customizable Alerts** (Planned):
   - Set alert thresholds and notification preferences.
5. **Dashboard** (Planned):
   - View status history, SSL expiry dates, and alerts.

## Technology Stack
- **Backend**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL (SQLite for testing)
- **Task Queue**: Celery with RabbitMQ
- **SSL Checking**: Python `socket` and `ssl` libraries
- **Notifications**: Twilio (SMS), Amazon SES (email), Slack SDK
- **Frontend**: TBD (likely React or HTMX)
- **Testing**: Pytest with Docker Compose

## Architecture & Flow
PulseCheck uses a modular architecture to ensure scalability and reliability:

- **Monitoring Service**: Uses `socket` to check SSL status and logs results in PostgreSQL.
- **Task Scheduler**: Celery runs periodic SSL checks daily at midnight, managed via RabbitMQ for queuing.
- **API Layer**: FastAPI exposes endpoints for SSL checks and log retrieval.
- **Database**: Stores website data and SSL logs (e.g., `SSLLog` table).
- **Notification Service** (Planned): Integrates with Twilio, SES, and Slack for alerts.

### Architecture Diagram
```mermaid
graph TD
    subgraph Frontend
        A[Future Dashboard] -->|API Calls| B[FastAPI Backend]
    end

    subgraph Backend
        B -->|Periodic Tasks| C[Celery Worker]
        B -->|Database Ops| D[PostgreSQL]
        C -->|Task Queue| E[RabbitMQ]
    end

    subgraph Monitoring
        F[SSL Checker socket] -->|Logs| D
        G[Uptime Checker HTTP] -->|Logs| D
        C -->|Triggers| F
        C -->|Triggers| G
    end

    subgraph Notifications
        B -->|Alerts| H[Twilio]
        B -->|Alerts| I[Amazon SES]
        B -->|Alerts| J[Slack]
    end

    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#f96,stroke:#333
    style D fill:#6f9,stroke:#333
    style E fill:#f66,stroke:#333
    style F fill:#9ff,stroke:#333
    style G fill:#9ff,stroke:#333
    style H fill:#69f,stroke:#333
    style I fill:#69f,stroke:#333
    style J fill:#69f,stroke:#333
```

### Flow
1. Users register websites via the API (planned UI).
2. Celery schedules daily SSL checks at midnight using RabbitMQ.
3. SSL status is checked with `socket`, logged in `SSLLog` model, and triggers notifications if needed.
4. API retrieves logs with pagination and filtering.

## Current Status
The project is under active development. Core SSL checking and logging are implemented, with uptime monitoring and notifications in progress.

## Getting Started
### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- RabbitMQ Message broker for Celery tasks (e.g., via `docker run -d -p 5672:5672 rabbitmq:3`)
- PostgreSQL Production database, with the `uuid-ossp` extension enabled for UUID generation (required for schema)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/MoigeMatino/pulse-check.git
   cd pulse-check
   ```
2. Set up environment (e.g., `.env` file):
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/pulsecheck
   RABBITMQ_URL=amqp://guest:guest@localhost:5672//
   ```
3. Run with Docker Compose:
   ```bash
   docker-compose up --build
   ```
4. Enable the `uuid-ossp` extension in PostgreSQL:
   ```bash
   docker-compose exec app psql -U user -d db_name -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
   ```
5. Apply database migrations:
   ```bash
   docker-compose exec app alembic upgrade head
   ```

### Usage
- **Check SSL Status**:
  ```bash
  curl -X GET "http://localhost:8000/check-ssl?url=https://example.com"
  ```
  Response:
  ```json
  {"valid": true, "expiry_date":"2026-01-15T23:59:59","days_remaining":288,"issuer": "DigiCert Global G3 TLS ECC SHA384 2020 CA1", "needs_renewal":False,"error":None}
  ```

- **Get SSL Logs**:
  ```bash
  curl -X GET "http://localhost:8000/websites/3/ssl-logs?limit=2"
  ```
  Response:
  ```json
  {
    "data": [
      {"id": 1, "website_id": "3", "timestamp": "2025-04-02T00:00:00Z", "valid_until": "2025-06-01T12:00:00Z", "issuer": "Let's Encrypt", "is_valid": true, "error": null}
    ],
    "next_cursor": null
  }
  ```
### Troubleshooting

- Migration Errors: If alembic upgrade head fails:
     - Ensure the `uuid-ossp` extension is installed (see step 4 above).
     - Reset the database with `docker-compose down -v` and retry the installation steps.
- Database Connection: Verify `DATABASE_URL` matches your PostgreSQL setup.

## Testing
Run tests in Docker:
```bash
docker-compose exec app pytest -s
```

## Documentation
For more details, check out the [wiki](https://github.com/MoigeMatino/pulse-check/wiki).

## License
Licensed under the [MIT License](LICENSE).
