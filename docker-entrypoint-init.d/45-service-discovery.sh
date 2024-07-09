#!/bin/bash

# Check for service discovery
if [[ -n "$DBMI_SERVICE_DISCOVERY_ENABLED" ]]; then

    # Get the current task ARN
    TASK_ARN=$(curl -sL ${ECS_CONTAINER_METADATA_URI_V4}/task | jq -r '.TaskARN')
    CLUSTER=$(curl -sL ${ECS_CONTAINER_METADATA_URI_V4}/task | jq -r '.Cluster')

    # Query for ECS service
    SERVICE=$(aws ecs describe-tasks --cluster $CLUSTER --tasks $TASK_ARN | jq -r '.tasks[0].group[8:]')

    # Query CloudMap for service
    SERVICE_ID=$(aws servicediscovery list-services | jq -r ".Services[] | select(.Name==\"$SERVICE\") | .Id")
    if [ ! -z $SERVICE_ID ]; then
        SERVICE_NAME=$(aws servicediscovery list-services | jq -r ".Services[] | select(.Name==\"$SERVICE\") | .Name")
        NAMESPACE_ID=$(aws servicediscovery get-service --id $SERVICE_ID | jq -r ".Service.NamespaceId")
        NAMESPACE_NAME=$(aws servicediscovery get-namespace --id $NAMESPACE_ID | jq -r ".Namespace.Properties.HttpProperties.HttpName")

        # Export the service domain
        echo "Service discovery service found: \"$SERVICE_NAME.$NAMESPACE_NAME\""
        export DBMI_SERVICE_DISCOVERY_NAMESPACE="$NAMESPACE_NAME"
        export DBMI_SERVICE_DISCOVERY_NAME="$SERVICE_NAME"
        export DBMI_SERVICE_DISCOVERY_DOMAIN="$SERVICE_NAME.$NAMESPACE_NAME"
    else
        echo "Service discovery service not found"
    fi
fi
