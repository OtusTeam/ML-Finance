```bash
docker build -t my-prometheus .
```
```bash
docker network create monitoring-net
```
```bash
docker run \
    --name prometheus-container \
    --network monitoring-net \
    -p 9090:9090 \
    -v ./prometheus_data:/prometheus \
    --restart always \
    my-prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/prometheus
```