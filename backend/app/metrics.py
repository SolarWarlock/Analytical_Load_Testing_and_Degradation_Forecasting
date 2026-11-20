from prometheus_client import Counter, Gauge, Histogram

EVENT_LOOP_LAG_BUCKETS = (
    0.0005,
    0.001,
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
)

HTTP_DURATION_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
)

EVENT_LOOP_LAG_SECONDS = Histogram(
    "fastapi_event_loop_lag_seconds",
    "Event loop scheduling lag in seconds",
    buckets=EVENT_LOOP_LAG_BUCKETS,
)

EVENT_LOOP_LAG_CURRENT_SECONDS = Gauge(
    "fastapi_event_loop_lag_current_seconds",
    "Latest measured event loop scheduling lag in seconds",
)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request processing duration in seconds",
    ["method", "endpoint"],
    buckets=HTTP_DURATION_BUCKETS,
)

DEGRADATION_LEAKED_MEMORY_BYTES = Gauge(
    "degradation_leaked_memory_bytes",
    "Simulated leaked memory held by the application in bytes",
)

DEGRADATION_BLOCKING_DELAY_SECONDS = Gauge(
    "degradation_blocking_delay_seconds",
    "Current synchronous blocking delay injected into workload in seconds",
)
