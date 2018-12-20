#!/bin/bash -e

# The wsgi to be run must be defined by user
:   ${DBMI_APP_WSGI?: must absolutely be defined, ya dingus!}
:   ${DBMI_APP_DOMAIN?: must absolutely be defined, ya dingus!}

# Check static file envs
if [ ! -z $DBMI_STATIC_FILES ]; then

:   ${DBMI_APP_STATIC_ROOT?: is required if static files are enabled}
:   ${DBMI_APP_STATIC_URL_PATH?: is required if static files are enabled}

fi

# Check file proxy envs
if [ ! -z $DBMI_FILE_PROXY ]; then

:   $DBMI_FILE_PROXY_PATH?: is required if file proxy is enabled}

fi

echo "Envs check passed!"

# Check for debug mode
if [ ! -z $DBMI_DEBUG ]; then

    # Dump envs
    echo -e "\nDBMI DEBUG: Dumping environment: \n"
    printenv

fi