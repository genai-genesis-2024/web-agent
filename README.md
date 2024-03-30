# web-agent

> Create Python Virtual Environment (Linux/Mac)

```
!python3 -m venv venv
!source venv/bin/activate
!pip install -r requirements.txt
```

> Set-up gcloud cli (Linux)

```
# Navigate to your home directory
!cd ~
!curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-468.0.0-linux-x86_64.tar.gz
!tar -xf google-cloud-cli-468.0.0-linux-x86_64.tar.gz
!./google-cloud-sdk/install.sh
# Open a new terminal
!gcloud auth login
# Please refer to Official Documentation for full details: https://cloud.google.com/sdk/docs/install-sdk
```

> Login with gloud cli (Vertex AI)

```
!gcloud auth application-default login
```
