from prometheus_client import Counter, Summary


metrics_labels = ["app_name", "app_version"]

app_metrics = {
    "request_time": Summary(
        "request_processing_seconds",
        "Time spent processing the request",
        metrics_labels + ["method", "http_status", "req_url"],
    )
}
