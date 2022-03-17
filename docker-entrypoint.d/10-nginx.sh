#!/usr/bin/dumb-init /bin/bash -e

# Check if nginx is running, reload it or start it
if [ -e $DBMI_NGINX_PID_PATH ]; then

    # Attempt to quit but ignore errors if Nginx isn't running
    nginx -s quit 2> /dev/null || true
fi

# Start Nginx
nginx
