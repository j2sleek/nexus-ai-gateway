import logging

logger = logging.getLogger(__name__)


def record_stream_event(event: str, provider: str, model: str, duration: float | None = None):
    # This is a stub for real metrics implementation (e.g., Prometheus)
    log_data = {"event": event, "provider": provider, "model": model}
    if duration is not None:
        log_data["duration"] = str(round(duration, 3))
    logger.info(f"Stream metrics: {log_data}")
