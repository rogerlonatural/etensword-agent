BUILD_VERION=20200801.0
PROJECT_ID=etensword-order-agent
SERVICE_NAME=agent-base

cd /Users/roger_lo/Documents/workspace/etensword-agent/docker/agent_base

gcloud builds submit --timeout=3600 --tag gcr.io/$PROJECT_ID/$SERVICE_NAME:$BUILD_VERION