#!/bin/bash -e

# Set the default region
export AWS_DEFAULT_REGION=${DBMI_AWS_REGION:=us-east-1}

# Check environment for secrets ID
if [[ -n $DBMI_SECRETS_MANAGER_ID ]]; then

    echo -e "Getting secrets for ID: $DBMI_SECRETS_MANAGER_ID\n"
    if [[ -n $DBMI_SECRETS_MANAGER_PRIORITY ]]; then
        # Run it
        echo -e "Will overwrite any existing environment with values from Secrets Manager\n"

        eval `aws secretsmanager get-secret-value \
                --secret-id ${DBMI_SECRETS_MANAGER_ID} \
                | jq -r '.SecretString' | jq -r 'to_entries \
                | .[] | "export \(.key | ascii_upcase)='\''\(.value)'\'';"'`

    else
        # Run
        echo -e "Will preserve existing environment over values from Secrets Manager\n"

        eval `aws secretsmanager get-secret-value \
                --secret-id ${DBMI_SECRETS_MANAGER_ID} \
                | jq -r '.SecretString' | jq -r 'to_entries \
                | .[] | "export \(.key | ascii_upcase)=${\(.key | ascii_upcase):-'\''\(.value)'\''};"'`
    fi
# Check environment for multiple secret IDs
elif [[ -n $DBMI_SECRETS_MANAGER_IDS ]]; then

    # Iterate through all IDs, if necessary
    for SM_ID in $(echo $DBMI_SECRETS_MANAGER_IDS | sed "s/,/ /g")
    do
        # Get the secrets
        echo -e "Getting secrets for ID: $SM_ID\n"
        if [[ -n $DBMI_SECRETS_MANAGER_PRIORITY ]]; then
            # Run it
            echo -e "Will overwrite any existing environment with values from Secrets Manager\n"

            eval `aws secretsmanager get-secret-value \
                    --secret-id ${SM_ID} \
                    | jq -r '.SecretString' | jq -r 'to_entries \
                    | .[] | "export \(.key | ascii_upcase)='\''\(.value)'\'';"'`

        else
            # Run
            echo -e "Will preserve existing environment over values from Secrets Manager\n"

            eval `aws secretsmanager get-secret-value \
                    --secret-id ${SM_ID} \
                    | jq -r '.SecretString' | jq -r 'to_entries \
                    | .[] | "export \(.key | ascii_upcase)=${\(.key | ascii_upcase):-'\''\(.value)'\''};"'`
        fi
    done
else
    echo -e "No Secrets Manager ID specified, nothing to do\n"
fi