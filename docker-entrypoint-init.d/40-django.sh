#!/bin/bash -e

# Check for static files
if [[ -n $DBMI_APP_DB ]]; then

    # Run migrations
    python ${DBMI_APP_ROOT}/manage.py migrate --no-input

fi

# Check for static files
if [[ -n $DBMI_STATIC_FILES ]]; then

    # Make the directory and collect static files
    mkdir -p "$DBMI_APP_STATIC_ROOT"
    python ${DBMI_APP_ROOT}/manage.py collectstatic --no-input

fi
