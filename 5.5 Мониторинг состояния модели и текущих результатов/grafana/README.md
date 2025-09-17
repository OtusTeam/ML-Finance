```bash
docker build -t my-grafana .
```


```bash
docker run \
    --name grafana-container \
    --network monitoring-net \
    -p 3000:3000 \
    -v ./grafana_data:/var/lib/grafana \
    --restart always \
    my-grafana
```