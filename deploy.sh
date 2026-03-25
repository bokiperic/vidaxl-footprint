#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Hunkemoller Digital Footprint — AWS Deployment Script
# Deploys EC2 t3.micro with Docker Compose (app + PostgreSQL) + Bedrock access
# ==============================================================================

REGION="eu-central-1"
INSTANCE_TYPE="t3.micro"
KEY_NAME="hunkemoller-footprint-key"
SG_NAME="hunkemoller-footprint-sg"
ROLE_NAME="hunkemoller-footprint-ec2-role"
PROFILE_NAME="hunkemoller-footprint-ec2-profile"
REPO_URL="https://github.com/bokiperic/vidaxl-footprint.git"

echo "==> Deploying Hunkemoller Digital Footprint to AWS ($REGION)"

# --- Check AWS CLI ---
if ! command -v aws &>/dev/null; then
    echo "ERROR: AWS CLI not found. Install it first: https://aws.amazon.com/cli/"
    exit 1
fi

# --- Detect deployer's public IP for SSH restriction ---
MY_IP=$(curl -s https://checkip.amazonaws.com | tr -d '[:space:]')
if [ -z "$MY_IP" ]; then
    echo "WARNING: Could not detect your public IP. SSH will be open to 0.0.0.0/0"
    SSH_CIDR="0.0.0.0/0"
else
    SSH_CIDR="${MY_IP}/32"
    echo "==> SSH will be restricted to your IP: $MY_IP"
fi

# --- Generate secure random credentials ---
DB_PASSWORD=$(openssl rand -base64 24 | tr -dc 'a-zA-Z0-9' | head -c 24)
API_KEY=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
AUTH_SECRET=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
echo "==> Generated random database password, API key, and auth secret"

# --- Get default VPC ---
VPC_ID=$(aws ec2 describe-vpcs --region "$REGION" \
    --filters Name=isDefault,Values=true \
    --query 'Vpcs[0].VpcId' --output text)
echo "==> Default VPC: $VPC_ID"

# --- Security Group ---
SG_ID=$(aws ec2 describe-security-groups --region "$REGION" \
    --filters Name=group-name,Values="$SG_NAME" Name=vpc-id,Values="$VPC_ID" \
    --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "None")

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
    echo "==> Creating security group..."
    SG_ID=$(aws ec2 create-security-group --region "$REGION" \
        --group-name "$SG_NAME" \
        --description "Hunkemoller Footprint - SSH + App" \
        --vpc-id "$VPC_ID" \
        --query 'GroupId' --output text)

    aws ec2 authorize-security-group-ingress --region "$REGION" \
        --group-id "$SG_ID" --protocol tcp --port 22 --cidr "$SSH_CIDR"
    aws ec2 authorize-security-group-ingress --region "$REGION" \
        --group-id "$SG_ID" --protocol tcp --port 8000 --cidr 0.0.0.0/0
    echo "==> Security group created: $SG_ID (SSH restricted to $SSH_CIDR)"
else
    echo "==> Security group exists: $SG_ID"
fi

# --- IAM Role + Instance Profile ---
if ! aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
    echo "==> Creating IAM role..."
    aws iam create-role --role-name "$ROLE_NAME" \
        --assume-role-policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }' --no-cli-pager

    aws iam put-role-policy --role-name "$ROLE_NAME" \
        --policy-name "bedrock-invoke" \
        --policy-document '{
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "arn:aws:bedrock:*::foundation-model/*"
            }]
        }'
    echo "==> IAM role created"
else
    echo "==> IAM role exists"
fi

if ! aws iam get-instance-profile --instance-profile-name "$PROFILE_NAME" &>/dev/null; then
    echo "==> Creating instance profile..."
    aws iam create-instance-profile --instance-profile-name "$PROFILE_NAME" --no-cli-pager
    aws iam add-role-to-instance-profile \
        --instance-profile-name "$PROFILE_NAME" \
        --role-name "$ROLE_NAME"
    echo "==> Waiting for instance profile propagation..."
    sleep 10
else
    echo "==> Instance profile exists"
fi

# --- Key Pair ---
if ! aws ec2 describe-key-pairs --region "$REGION" --key-names "$KEY_NAME" &>/dev/null; then
    echo "==> Creating key pair..."
    aws ec2 create-key-pair --region "$REGION" \
        --key-name "$KEY_NAME" \
        --query 'KeyMaterial' --output text > "${KEY_NAME}.pem"
    chmod 400 "${KEY_NAME}.pem"
    echo "==> Key pair saved to ${KEY_NAME}.pem"
else
    echo "==> Key pair exists"
fi

# --- AMI: Amazon Linux 2023 ---
AMI_ID=$(aws ec2 describe-images --region "$REGION" \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-2023.*-x86_64" "Name=state,Values=available" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text)
echo "==> Using AMI: $AMI_ID"

# --- User Data Script ---
# Note: We use a heredoc without quoting to allow variable substitution for secrets
USER_DATA=$(cat <<USERDATA
#!/bin/bash
set -ex

# Swap (1GB) for t3.micro
dd if=/dev/zero of=/swapfile bs=1M count=1024
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile swap swap defaults 0 0' >> /etc/fstab

# Install Docker
dnf install -y docker git
systemctl enable docker
systemctl start docker

# Install Docker Compose plugin
mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \\
    -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Clone repo
cd /opt
git clone ${REPO_URL} app
cd app

# Create .env for production with generated secrets
cat > .env <<ENVEOF
USE_BEDROCK=true
AWS_REGION=eu-central-1
BEDROCK_MODEL_ID=eu.anthropic.claude-3-haiku-20240307-v1:0
ANTHROPIC_API_KEY=
APP_ENV=production
POSTGRES_USER=vidaxl
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=vidaxl_footprint
API_KEY=${API_KEY}
AUTH_USERNAME=levi9Hunkemoller
AUTH_PASSWORD=Hunk3moll3r!
AUTH_SECRET=${AUTH_SECRET}
ENVEOF

# Build and start with production compose
docker compose -f docker-compose.prod.yml up --build -d

USERDATA
)

# --- Launch EC2 ---
echo "==> Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances --region "$REGION" \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --iam-instance-profile Name="$PROFILE_NAME" \
    --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":8,"VolumeType":"gp3","Encrypted":true}}]' \
    --user-data "$USER_DATA" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=hunkemoller-footprint}]" \
    --query 'Instances[0].InstanceId' --output text)

echo "==> Instance launched: $INSTANCE_ID"
echo "==> Waiting for instance to be running..."
aws ec2 wait instance-running --region "$REGION" --instance-ids "$INSTANCE_ID"

PUBLIC_IP=$(aws ec2 describe-instances --region "$REGION" \
    --instance-ids "$INSTANCE_ID" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo ""
echo "=============================================="
echo "  Deployment Complete!"
echo "=============================================="
echo "  Instance ID:  $INSTANCE_ID"
echo "  Public IP:    $PUBLIC_IP"
echo "  Dashboard:    http://$PUBLIC_IP:8000/dashboard"
echo "  SSH:          ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo ""
echo "  CREDENTIALS (save these — not recoverable):"
echo "  DB Password:  $DB_PASSWORD"
echo "  API Key:      $API_KEY"
echo ""
echo "  API Usage:    curl -H 'X-API-Key: $API_KEY' http://$PUBLIC_IP:8000/api/v1/scrape/run -X POST"
echo ""
echo "  NOTE: Wait ~3-5 minutes for Docker build to complete."
echo "  Check progress: ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP 'sudo cloud-init status'"
echo ""
echo "  IMPORTANT: Enable Bedrock model access in AWS Console:"
echo "  Console -> Amazon Bedrock -> Model access -> Enable Claude 3 Haiku"
echo "=============================================="
