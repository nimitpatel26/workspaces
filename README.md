

# URL Shortner

## Overview
* The service is hosted on apps platform.
* https://cloud.digitalocean.com/apps/047a71f0-b0ac-4180-93a6-524970bf1664/deployments?i=96b814

* GitHub Repository:
* https://github.com/nimitpatel26/workspaces


## Routes
1. GET /
    - Hello Wordld
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