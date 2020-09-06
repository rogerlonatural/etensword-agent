docker run --rm -it \
  -v /Users/roger_lo/Documents/workspace/etensword-agent/:/app/ \
  -v /Users/roger_lo/Documents/workspace/etensword-agent/docker/roger_shioaji/.cert/:/app/config/ \
  -e PORT=8080 \
  -e ETENSWORD_AGENT_CONF=/app/config/agent_settings.ini \
  gcr.io/etensword-order-agent/agent-app:local
