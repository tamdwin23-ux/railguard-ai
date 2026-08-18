# RailGuard AI

RailGuard AI is a cloud-based predictive maintenance and failure intelligence platform built using the MetroPT-3 industrial air-compressor dataset.

## Architecture

MetroPT Sensors → FastAPI → AWS S3 → Feature Engineering → ML Models → Risk Engine → CloudWatch → n8n → Maintenance Alert

## ML Pipeline

- 1,516,948 raw sensor readings
- 15 equipment signals
- 1-minute feature aggregation
- 30-minute rolling trend features
- 57 production ML features
- Global Isolation Forest anomaly model
- KMeans operating-regime detection
- Regime-specific anomaly models
- Runtime persistent-fault confirmation
- Feature-level anomaly explanations
- Feature drift monitoring

## Risk States

- LOW — normal behaviour
- WATCH — regime-specific anomaly
- HIGH — global anomaly
- DUAL — global and regime anomaly
- CRITICAL — persistent fault confirmed

## Validation

Production pipeline replay against the four documented MetroPT failure periods:

| Failure | Result |
|---|---|
| F1 | Confirmed 42 min after failure start |
| F2 | Confirmed 4 min after failure start |
| F3 | Confirmed 9 min after failure start |
| F4 | Confirmed 38 min before failure start |

All four documented failure periods produced confirmed fault incidents.

These are engineering validation results against the documented MetroPT failure windows and do not claim universal early-failure prediction.

## Technology

Python · Pandas · NumPy · scikit-learn · FastAPI · Docker · AWS EC2 · S3 · IAM · CloudWatch · Nginx · n8n · GitHub Actions · Terraform

## Production Infrastructure

- FastAPI inference API
- Docker deployment on AWS EC2
- Nginx reverse proxy
- IAM role-based AWS access
- Raw telemetry storage in S3
- Prediction and drift-event storage in S3
- CloudWatch infrastructure metrics
- CloudWatch API and Nginx logs
- High-memory CloudWatch alarm
- n8n automated maintenance alerts

## API

- `GET /health`
- `GET /model-info`
- `GET /required-features`
- `POST /predict`
- `POST /predict-risk`
- `POST /ingest`
- `POST /resolve-fault`

## Status

Completed: ML pipeline, API, Docker, AWS S3, CloudWatch, Nginx and n8n maintenance automation.

Next: GitHub Actions CI/CD and Terraform Infrastructure as Code.
