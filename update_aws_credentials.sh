#!/bin/bash
# update_aws_credentials.sh
# Script to update AWS credentials in .env file when they expire

echo "AWS Credential Updater for Foodosis"
echo "===================================="
echo "This script helps you update expired AWS Learner Lab credentials"
echo ""

# Prompt for new credentials
read -p "Enter new AWS_ACCESS_KEY_ID: " NEW_ACCESS_KEY
read -p "Enter new AWS_SECRET_ACCESS_KEY: " NEW_SECRET_KEY
read -p "Enter new AWS_SESSION_TOKEN: " NEW_SESSION_TOKEN

# Backup current .env
cp .env .env.backup
echo "✓ Created backup: .env.backup"

# Update .env file
sed -i "s/AWS_ACCESS_KEY_ID=.*/AWS_ACCESS_KEY_ID=$NEW_ACCESS_KEY/" .env
sed -i "s/AWS_SECRET_ACCESS_KEY=.*/AWS_SECRET_ACCESS_KEY=$NEW_SECRET_KEY/" .env
sed -i "s/AWS_SESSION_TOKEN=.*/AWS_SESSION_TOKEN=$NEW_SESSION_TOKEN/" .env

echo "✓ Updated .env file with new credentials"

# Show what was updated (without revealing full credentials)
echo ""
echo "Updated credentials:"
echo "AWS_ACCESS_KEY_ID: ${NEW_ACCESS_KEY:0:10}..."
echo "AWS_SECRET_ACCESS_KEY: ${NEW_SECRET_KEY:0:10}..."
echo "AWS_SESSION_TOKEN: ${NEW_SESSION_TOKEN:0:20}..."

# Test the credentials
echo ""
echo "Testing new credentials..."
python3 -c "
import boto3
import os
from dotenv import load_dotenv
load_dotenv()

try:
    s3 = boto3.client('s3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
        region_name=os.getenv('AWS_REGION')
    )
    s3.list_buckets()
    print('✓ AWS credentials are valid!')
except Exception as e:
    print('❌ AWS credentials test failed:', str(e))
    print('Rolling back to previous .env...')
    import subprocess
    subprocess.run(['cp', '.env.backup', '.env'])
    exit(1)
"

# If we get here, credentials are good
echo ""
echo "Now commit and push the updated .env:"
echo "  git add .env"
echo "  git commit -m 'Update AWS Learner Lab credentials'"
echo "  git push"
echo ""
echo "This will automatically trigger Jenkins to deploy with new credentials!"