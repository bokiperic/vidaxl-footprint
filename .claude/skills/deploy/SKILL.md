---
name: deploy
description: Deploy or redeploy the application to the AWS EC2 production server. Runs pre-deploy checks, pulls latest code, rebuilds Docker containers, and verifies the deployment.
disable-model-invocation: true
allowed-tools: Bash, Read, Glob, Grep
---

# Deploy to AWS

Deploy the Hunkemoller Digital Footprint application to the AWS EC2 production server.

## Server Details

- **Host:** `35.159.197.144`
- **SSH Key:** `hunkemoller-footprint-key.pem`
- **SSH User:** `ec2-user`
- **App directory:** `/opt/app`
- **Compose file:** `docker-compose.prod.yml`

## Steps

### 1. Pre-deploy checks (run locally)

- Run `git status` to ensure there are no uncommitted changes. If there are uncommitted changes, STOP and ask the user to commit first (suggest using `/commit-and-push`).
- Run `git log origin/main..HEAD` to check for unpushed commits. If there are unpushed commits, STOP and ask the user to push first.

### 2. Deploy to EC2

SSH into the server and run the following commands sequentially:

```bash
ssh -i hunkemoller-footprint-key.pem -o StrictHostKeyChecking=no ec2-user@35.159.197.144 \
  'cd /opt/app && sudo git pull origin main && sudo docker compose -f docker-compose.prod.yml up --build -d'
```

Use a timeout of 300000ms (5 minutes) for the deploy command since Docker builds can take time.

### 3. Post-deploy verification

After deployment, verify the app is running:

```bash
ssh -i hunkemoller-footprint-key.pem -o StrictHostKeyChecking=no ec2-user@35.159.197.144 \
  'sudo docker ps && curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/'
```

- Confirm both `app-app-1` and `app-db-1` containers are running and healthy.
- Confirm the HTTP response code is `200` or `303` (redirect to login).

### 4. Check for startup errors

```bash
ssh -i hunkemoller-footprint-key.pem -o StrictHostKeyChecking=no ec2-user@35.159.197.144 \
  'sudo docker logs app-app-1 2>&1 | tail -20'
```

- If there are errors in the logs, report them to the user.

### 5. Report

Summarize:
- Whether deployment succeeded
- Container status
- Any warnings or errors from logs
- The live URL: `http://35.159.197.144`

If any step fails, stop and report the error immediately. Do not retry automatically.
