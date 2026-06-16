

# URL Shortner

## Overview

### GitHub Repository:
* https://github.com/nimitpatel26/workspaces

### Postgres Database:
* https://cloud.digitalocean.com/databases/3d3aca0e-bea8-4afb-90fa-34bca4d243a5?i=96b814
* In prod settings, I wouldn't put the connection string here.
* How to place in environment variables:
* `export DB_CONNECTION_STRING="postgresql://doadmin:AVNS_KPfSD8o1CpwrY2XGeGH@tiny-url-do-user-33622398-0.g.db.ondigitalocean.com:25060/defaultdb?sslmode=require"`

### The service is hosted on apps platform.
* https://cloud.digitalocean.com/apps/047a71f0-b0ac-4180-93a6-524970bf1664/deployments?i=96b814

## Routes
1. GET /
    - Hello World
    - Health Check

2. POST /tiny-url/create
    - Body:
        `{
            "longUrl": "https://google.com",
            "customAlias": "google-home"
        }`

3. POST /tiny-url/metadata/{alias}
    - Get the metadata.

4. POST /redirect/{alias}
    - Redirect to the long URL.

![Alt text](./create_api.png)