# Setup

```bash
conda env create -f conda_env.yml
GOOGLE_APPLICATION_CREDENTIALS=./lucid-inquiry-205018-7b6986d494b4.json python generate_demo_page.py
```

# Updating the ACL
```bash
gsutil acl ch -R -u AllUsers:R gs://gibsonchallenge/behavior_demonstrations
```
