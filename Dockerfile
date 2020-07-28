FROM gcr.io/etensword-order-agent/agent-base:2020.07.26.0

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME

ENV ETENSWORD_AGENT_CONF /app/config/agent_settings.ini

COPY . ./

RUN pip install /app/

