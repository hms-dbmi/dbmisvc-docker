#!/usr/bin/env bash
set -e

# Check for AWS EC2 internal endpoint
if [[ -n $DBMI_LB ]]; then

    # Determine launch type
    DBMI_ECS_LAUNCH_TYPE="$(curl -sL ${ECS_CONTAINER_METADATA_URI_V4}/task | jq -r '.LaunchType')"

    # Check for ECS type of deployment
    if [[ $DBMI_ECS_LAUNCH_TYPE == "FARGATE" ]]; then

        # This is being deployed via ECS Fargate

        # Get the IP address of this task
        DBMI_FARGATE_ENI="$(curl -sL ${ECS_CONTAINER_METADATA_URI_V4} | jq -r '.Networks[0].IPv4Addresses[0]')"
        export DBMI_FARGATE_ENI
        export ALLOWED_HOSTS="$ALLOWED_HOSTS,$DBMI_FARGATE_ENI"

        # Get subnet DNS
        DBMI_FILE_PROXY_DNS="$(curl -sL ${ECS_CONTAINER_METADATA_URI_V4} | jq -r '.Networks[0].DomainNameServers[0]')"
        export DBMI_FILE_PROXY_DNS

    elif [[ $DBMI_ECS_LAUNCH_TYPE == "EC2" ]]; then

        # This is being deployed via ECS EC2

        # Set API IP
        AWS_IMDS_ENDPOINT="http://169.254.169.254"

        # Check what version of IMDS is required
        declare -a CURL_ARGS=('-sL')
        if [[ $(curl "${CURL_ARGS[@]}" -w "%{http_code}\n" ${AWS_IMDS_ENDPOINT}) == "401" ]]; then

            # Get the AWS IMDSv2 session token
            TOKEN="$(curl "${CURL_ARGS[@]}" -X PUT "${AWS_IMDS_ENDPOINT}/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300")"
            CURL_ARGS+=('-H' "X-aws-ec2-metadata-token: $TOKEN")

        fi

        # Get the EC2 host IP
        DBMI_EC2_HOST="$(curl "${CURL_ARGS[@]}" "${AWS_IMDS_ENDPOINT}/latest/meta-data/local-ipv4")"
        export DBMI_EC2_HOST
        export ALLOWED_HOSTS="$ALLOWED_HOSTS,$DBMI_EC2_HOST"

        # Set the trusted addresses for load balancers to the current subnet
        DBMI_EC2_MAC="$(curl "${CURL_ARGS[@]}" "${AWS_IMDS_ENDPOINT}/latest/meta-data/mac")"
        DBMI_LB_SUBNET="$(curl "${CURL_ARGS[@]}" "${AWS_IMDS_ENDPOINT}/latest/meta-data/network/interfaces/macs/${DBMI_EC2_MAC}/vpc-ipv4-cidr-blocks")"
        export DBMI_LB_SUBNET

        # Get the address of the VPC's primary DNS resolver
        DBMI_VPC_CIDR_BLOCK="$(curl "${CURL_ARGS[@]}" "${AWS_IMDS_ENDPOINT}/latest/meta-data/network/interfaces/macs/${DBMI_EC2_MAC}/vpc-ipv4-cidr-block")"

        # Primary DNS resolver for VPC is first IP in CIDR block plus 2 (e.g. 10.0.0.0/16 -> 10.0.0.2)
        # This simply uses prips to print all IP addresses in block and extracts the third one.
        DBMI_FILE_PROXY_DNS=$(prips "${DBMI_VPC_CIDR_BLOCK}" | sed -n 3p)
        export DBMI_FILE_PROXY_DNS

    fi
fi

# Check for service discovery
if [[ -n "$DBMI_SERVICE_DISCOVERY_DOMAIN" ]]; then

    # Add wildcard service discovery domain to allowed hosts
    export ALLOWED_HOSTS="$ALLOWED_HOSTS,.$DBMI_SERVICE_DISCOVERY_DOMAIN"
fi

# Check for self signed
if [[ -n "$DBMI_CREATE_SSL" ]]; then

    # Set defaults
    export DBMI_SSL_PATH=${DBMI_SSL_PATH:=/etc/nginx/ssl}
    DBMI_APP_DOMAIN=${DBMI_APP_DOMAIN:=localhost}

    # Set the wildcarded domain we want to use
    commonname="*.${DBMI_APP_DOMAIN}"

    # Ensure the directory exists
    mkdir -p ${DBMI_SSL_PATH}

    # A blank passphrase
    passphrase="$(openssl rand -base64 15)"
    country=US
    state=Massachusetts
    locality=Boston
    organization=HMS
    organizationalunit=DBMI
    email=admin@hms.harvard.edu

    # Generate our Private Key, CSR and Certificate
    openssl genrsa -out "${DBMI_SSL_PATH}/${DBMI_APP_DOMAIN}.key" 2048
    openssl req -new -key "${DBMI_SSL_PATH}/${DBMI_APP_DOMAIN}.key" -out "${DBMI_SSL_PATH}/${DBMI_APP_DOMAIN}.csr" -passin pass:"${passphrase}" -subj "/C=$country/ST=$state/L=$locality/O=$organization/OU=$organizationalunit/CN=$commonname/emailAddress=$email"
    openssl x509 -req -days 365 -in "${DBMI_SSL_PATH}/${DBMI_APP_DOMAIN}.csr" -signkey "${DBMI_SSL_PATH}/${DBMI_APP_DOMAIN}.key" -out "${DBMI_SSL_PATH}/${DBMI_APP_DOMAIN}.crt"
fi

# Check for service discovery
if [[ -n "$DBMI_SERVICE_DISCOVERY_DOMAIN" ]] && [[ -n "$DBMI_SERVICE_DISCOVERY_SSL" ]]; then

    # Set the wildcarded domain we want to use
    commonname="*.${DBMI_SERVICE_DISCOVERY_DOMAIN}"

    # A blank passphrase
    passphrase="$(openssl rand -base64 15)"
    country=US
    state=Massachusetts
    locality=Boston
    organization=HMS
    organizationalunit=DBMI
    email=admin@hms.harvard.edu

    # Generate our Private Key, CSR and Certificate
    openssl genrsa -out "${DBMI_SSL_PATH}/${DBMI_SERVICE_DISCOVERY_DOMAIN}.key" 2048
    openssl req -new -key "${DBMI_SSL_PATH}/${DBMI_SERVICE_DISCOVERY_DOMAIN}.key" -out "${DBMI_SSL_PATH}/${DBMI_SERVICE_DISCOVERY_DOMAIN}.csr" -passin pass:"${passphrase}" -subj "/C=$country/ST=$state/L=$locality/O=$organization/OU=$organizationalunit/CN=$commonname/emailAddress=$email"
    openssl x509 -req -days 365 -in "${DBMI_SSL_PATH}/${DBMI_SERVICE_DISCOVERY_DOMAIN}.csr" -signkey "${DBMI_SSL_PATH}/${DBMI_SERVICE_DISCOVERY_DOMAIN}.key" -out "${DBMI_SSL_PATH}/${DBMI_SERVICE_DISCOVERY_DOMAIN}.crt"

fi

if [[ -n "$DBMI_SSL" ]]; then

    # Set defaults
    export DBMI_SSL_PATH=${DBMI_SSL_PATH:=/etc/nginx/ssl}

    # Ensure the directory exists
    mkdir -p ${DBMI_SSL_PATH}

    # Also create a wildcard certificate for errant requests
    passphrase="$(openssl rand -base64 15)"
    commonname="*"
    country=US
    state=Massachusetts
    locality=Boston
    organization=Nothing
    organizationalunit=Default
    email=nothing@default.com
    openssl genrsa -out "${DBMI_SSL_PATH}/default.key" 2048
    openssl req -new -key "${DBMI_SSL_PATH}/default.key" -out "${DBMI_SSL_PATH}/default.csr" -passin pass:"${passphrase}" -subj "/C=$country/ST=$state/L=$locality/O=$organization/OU=$organizationalunit/CN=$commonname/emailAddress=$email"
    openssl x509 -req -days 365 -in "${DBMI_SSL_PATH}/default.csr" -signkey "${DBMI_SSL_PATH}/default.key" -out "${DBMI_SSL_PATH}/default.crt"

fi

# Set base directory for nginx configuration files
DBMI_CONFIG_PATH=${DBMI_CONFIG_PATH:=/etc/nginx/conf.d}
mkdir -p $DBMI_CONFIG_PATH

# Setup the nginx and site configuration
j2 /docker-entrypoint-templates.d/nginx.healthcheck.conf.j2 > $DBMI_CONFIG_PATH/nginx.healthcheck.conf
j2 /docker-entrypoint-templates.d/nginx.proxy.conf.j2 > $DBMI_CONFIG_PATH/nginx.proxy.conf
j2 /docker-entrypoint-templates.d/nginx.conf.j2 > /etc/nginx/nginx.conf
