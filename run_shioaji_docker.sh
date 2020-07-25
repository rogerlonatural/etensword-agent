docker run --rm -it \
  -v /Users/roger_lo/Documents/workspace/etensword-agent:/home/work/etensword-agent \
  -v /Users/roger_lo/Documents/workspace/etensword-agent/.cert/:/home/work/conf/ \
  -e ETENSWORD_AGENT_CONF=/home/work/conf/agent_settings.ini \
  etensword-agent-shioaji-api:latest
