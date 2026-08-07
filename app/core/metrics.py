from fastapi import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

REQUEST_COUNT = Counter("gateway_requests_total", "Total requests", ["method", "path", "status"])
REQUEST_DURATION = Histogram(
    "gateway_request_duration_seconds", "Request duration", ["method", "path"]
)
PROVIDER_FAILURES = Counter(
    "gateway_provider_failures_total", "Provider failures", ["provider", "model"]
)


def get_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
