FROM python:3.6-alpine3.8 AS builder

# Install dependencies
RUN apk add --update \
    build-base \
    g++

# Install Python packages
RUN pip install awscli boto3 shinto-cli dumb-init gunicorn

FROM python:3.6-alpine3.8

RUN apk add --no-cache --update \
    bash \
    nginx \
    curl \
    openssl \
    jq \
  && rm -rf /var/cache/apk/*

# Copy pip packages from builder
COPY --from=builder /root/.cache /root/.cache

# Install some pip packages
RUN pip install awscli boto3 shinto-cli dumb-init gunicorn

# Copy scripts, templates and resources
ADD docker-entrypoint-templates.d/ /docker-entrypoint-templates.d/
ADD docker-entrypoint-resources.d/ /docker-entrypoint-resources.d/
ADD docker-entrypoint-init.d/ /docker-entrypoint-init.d/
ADD docker-entrypoint.d/ /docker-entrypoint.d/

# Add the init script and make it executable
ADD docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod a+x docker-entrypoint.sh

ENTRYPOINT ["dumb-init", "/docker-entrypoint.sh"]

CMD gunicorn ${DBMI_APP_WSGI}.wsgi:application -b unix:/tmp/gunicorn.sock \
    --user ${DBMI_NGINX_USER} --group ${DBMI_NGINX_USER} --chdir=${DBMI_APP_ROOT}