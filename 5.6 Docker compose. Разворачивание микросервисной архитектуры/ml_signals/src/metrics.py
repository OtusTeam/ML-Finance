from prometheus_client import Counter, Summary


metrics_labels = ["app_name", "app_version"]

app_metrics = {
    "request_time": Summary(
        "request_processing_seconds",
        "Time spent processing the request",
        metrics_labels + ["method", "http_status", "req_url"],
    ),
    "ml_model_prediction_time": Summary(
        "ml_predictions_time", "Time spent on model prediction", metrics_labels + ["model_name", "model_version"]
    ),
    "total_order_execution_latency_time": Summary(
        "order_execution_seconds",
        "Time spent from receiving data to executing the order",
        metrics_labels + ["model_name", "model_version"],
    ),
    "calculating_signal_time": Summary(
        "signal_calculating_seconds",
        "Time spent calculating the signal",
        metrics_labels + ["model_name", "model_version"],
    ),
    "signals_counter": Counter(
        "signals_counter",
        "Counter of signals",
        metrics_labels + ["model_name", "model_version", "signal"],
    ),
    "mae": Summary(
        "mae",
        "Mean Absolute Error one sample",
        metrics_labels + ["model_name", "model_version", "signal"],
    ),
}
