# Deployment Documentation

## Local Deployment

1. Clone the repository.
2. Create a virtual environment: `python -m venv .venv`
3. Activate: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Configure `.env` (see `.env.example`)
6. Run: `uvicorn app.main:app --reload`

## Docker Deployment

Build the image:
```bash
docker build -t nexus-ai-gateway:v1.0.0 .
```

Run with Docker Compose:
```bash
docker-compose up -d
```

## Production Configuration

- **Environment**: Set `ENVIRONMENT=production`
- **Security**: Always use a secure `X-API-Key` and update `config/auth.yaml` before deployment.
- **Metrics**: Ensure `metrics_public` is `false` in `config/auth.yaml` for production.

## Scaling

For high traffic, deploy multiple replicas behind a load balancer. The stateless nature of the gateway allows easy horizontal scaling.

## Security Checklist

- [ ] API keys updated in `config/auth.yaml`
- [ ] `metrics_public` set to `false`
- [ ] Environment variables secured (do not commit `.env`)
- [ ] CORS policies configured (if applicable)
