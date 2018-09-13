FROM python:3.6-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        nginx \
        jq \
        curl \
        openssl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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

CMD gunicorn ${DBMI_APP_WSGI}.wsgi:application -b 0.0.0.0:${DBMI_GUNICORN_PORT} \
    --user ${DBMI_NGINX_USER} --group ${DBMI_NGINX_USER} --chdir=${DBMI_APP_ROOT}