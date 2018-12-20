DBMI Service Container
---

Configuration
-----------------

This image configures itself based on the values of variables either defined in the environment through the Docker context, or fetched
from AWS Parameter Store or AWS Secrets Manager (in progress) during initialization.

The following is a summary of these variables used to configure the container and their expected values. Default values are provided for a common
configuration with the exception of the required variables immediately following.

Required App Variables
---------------------

| Variable | Description | Example |
| -------- | ----------- | ------- |
| `DBMI_APP_WSGI` | The WSGI module name to pass Gunicorn, excluding extension | `project_name` |
| `DBMI_APP_DOMAIN` | The domain to use for nginx configurations and SSL naming. If *.crt and *.key are provided manually, they must be placed in `DBMI_SSL_ROOT` and named {`DBMI_APP_DOMAIN`}.{crt&#124;key} |` app.domain.com` |

Nginx and Gunicorn
---------------------

Miscellaneous parameters for the configuration of nginx and Gunicorn

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `DBMI_PORT` | Configures the port to expose nginx on | `80` |
| `DBMI_NGINX_USER` | The user under which to run nginx (default: nginx) | `nginx` |
| `DBMI_NGINX_PID_PATH` | The path to the process file for nginx | `/var/run/nginx.pid` | 
| `DBMI_GUNICORN_SETTINGS` | Additional settings to pass to gunicorn | ` ` |

Secrets
---------------

| Variable | Description | Example |
| -------- | ----------- | ------- |
| `DBMI_PARAMETER_STORE_PATH` | The path to fetch Parameter Store secrets from | `/com/domain/app/dev` |
| `DBMI_PARAMETER_STORE_PREFIX` | The prefix to fetch Parameter Store secrets from | `com.domain.app.dev` |
| `DBMI_PARAMETER_STORE_PRIORITY` | Whether to allow environment specified at runtime to override those fetched from Parameter Store | `false` |


Secrets are currently loaded from AWS Parameter Store in a typical configuration. Your image/environment will need to
specify the path/prefix under which your app's secrets are stored. Upon initialization, the init scripts will fetch
all secrets in the specified location and will place them in the process environment. Django can then pull those
variables from environment in the settings module. Since environment can also be defined at runtime through
the Docker context, `DBMI_PARAMETER_STORE_PRIORITY` is intended to set priority of the source of secrets. If this
flag is set to `true`, any locally defined variables can be overwritten by values fetched from Parameter Store. This
allows setting default values in the image or at runtime, but ultimately using whatever is stored in Parameter Store.
Flipping this flag allows one to override configurations at runtime. Useful for running the container in a development/testing
environment where tweaks are needed.

SSL
------

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `DBMI_SSL` | Whether to setup SSL or not | `false` |
| `DBMI_CREATE_SSL` | Whether to create a self-signed SSL for usage behind a proxy | `false` |
| `DBMI_SSL_PATH` | The path to where certificate and key are placed | `/etc/nginx/ssl` |

This image is configured to enable/disable SSL in nginx, and if enabled, generate self-signed certificates or use
certificates provided by some other means. Self-signed certificates are typically used behind ELBs where the actual
SSL termination is done on the load balancer, and the self-signed certificates are merely a means to keep traffic
encrypted internally. If certificates are to be provided manually, be sure to place the certificate and key files
in the specified `DBMI_NGINX_SSL_PATH` and name them `{DBMI_APP_DOMAIN}.crt` and `{DBMI_APP_DOMAIN}.key`, respectively.

Healthchecks
---------------

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `DBMI_HEALTHCHECK` | Whether to define healthcheck endpoints in nginx | `true` |
| `DBMI_APP_HEALTHCHECK_PATH` | The path at which healthcheck requests can be made to the Django instance | `/healthcheck` |

In a typical ECS/ELB environment, your app needs to respond to healthchecks from the local Docker daemon, as well 
as from the ELB. This means requests will be made to your application with the host header set to `localhost` as well
as your ECS instance's internal IP. Django must be configured to allow these requests as well as those directed to
your app's actual host. Those three hosts are automatically configured into the `ALLOWED_HOSTS` variable, intended to
be used for the Django setting.

Healthcheck endpoints are also setup to be handled separately from application requests. This prevents nginx logs from being 
filled with healthcheck requests and also ensures the endpoint is only accessible locally and from the ELB instance's 
subnet.

Application Load Balancer
-------------------------

| Variable | Description | Example |
| -------- | ----------- | ------- |
| `DBMI_LB` | Whether the application should be configured for an ALB | `true` |
| `DBMI_HEALTHCHECK_PATH` | The path at which healthcheck requests can be sent from the ELB | `/healthcheck` |

The current configuration is only setup to work behind an AWS Application Load Balancer. This configuration involves
providing a healthcheck endpoint as well as ensuring the original request headers are used for logging.

Static Files
-------------

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `DBMI_STATIC_FILES` | Whether static files should be managed and served | `false` |
| `DBMI_APP_STATIC_ROOT` | The absolute path to the directory containing all static files to be served by nginx. This is only required if `DBMI_STATIC_FILES` is set as `true` | `/app/static` |
| `DBMI_APP_STATIC_URL_PATH` | The path at which nginx will server static files | `/static` |

If required, static files configurations are made within nginx to serve those files directly. If serving static files,
 `DBMI_APP_STATIC_ROOT` must be configured to set the absolute path to where static files are collected in the container.
 `DBMI_APP_STATIC_URL_PATH` then specifies the URL path that nginx will handle as the static files location, where it
 will attempt to server the requested file in the `DBMI_APP_STATIC_ROOT`.
 
 File Proxy
 -----------
 
| Variable | Description | Default |
| -------- | ----------- | ------- |
| `DBMI_FILE_PROXY` | Whether to enable to location for file proxy requests | `false` |
| `DBMI_FILE_PROXY_PATH` | The URL path to use for file proxies from S3 | `/proxy` |

 For an application that provides downloads of file that are stored in AWS S3, the file proxy enables an endpoint to
 seamlessly proxy files from S3 to the requesting user without requiring storage of the file within the container. 
 `DBMI_FILE_PROXY_PATH` specifies the root path of URLs that when sent to nginx, will be redirected by nginx to the S3
 file and the contents of that file will then be passed through nginx to the user. For this to work, your application
 will need to set the `X-Accel` header to: 
```
 https://{DBMI_APP_DOMAIN}/{DBMI_FILE_PROXY_PATH}/{S3 bucket name}/{S3 signed URL's path and query}
```
 When handling a request to this URL, nginx pulls the S3 bucket name, path and query from the URL, assembles it
 back into the original signed S3 download URL, proxies that request to S3, and then passes the response directly
 back to the requesting user.
 
 As an example, my app manages an S3 file named `my_file.txt`. If a user wants to download that file, they make a request to
 `https://app.domain.com/download/my_file.txt`. My application receives that request, performs any authentication and/or
 authorization and logging, and if permitted, prepares to return the file. To do this, the app generates the signed S3
 URL, that would look something like:
 ```
 https://my-bucket.s3.amazonaws.com/34bde615-2861-4f70-816a-6c5f7304a824/my_file.txt?Signature=A8DIf5FUUZsv1sxACTi0Q%2B7H4VI%3D&Expires=1545316868&AWSAccessKeyId=AKIFAPCDZOQ77R9EL9DO
```
My app then prepares an empty response, setting the `X-Accel` header to the magic URL, that would look something like:
 ```
 /proxy/https/my-bucket.s3.amazonaws.com/34bde615-2861-4f70-816a-6c5f7304a824/my_file.txt?Signature=A8DIf5FUUZsv1sxACTi0Q%2B7H4VI%3D&Expires=1545316868&AWSAccessKeyId=AKIFAPCDZOQ77R9EL9DO
```
When nginx receives this response, it takes the URL and assembles the components (protocol, path, query) back into the
original signed S3 URL. It then proxies the request to that URL, and whatever comes back from S3, is passed through nginx
directly to the origin of the request.

Your application accepts and passes through the download request, if allowed, and nginx handles the rest of the download
on its own. Nifty!

