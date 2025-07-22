# Foodosis - Inventory Management System for Food and Beverage Manufacturing

## Overview
Foodosis is a simple inventory management app built for the Cloud Platform Programming module. It uses 5 AWS services programmatically: S3 (file storage), RDS (data), Lambda (logic), SNS (notifications), CloudWatch (scheduling/logging). Tech stack: Python, Flask, HTML/CSS/Bootstrap/JavaScript. Reusable library: foodosis_aws_utils.

## Setup Instructions
1. Activate virtualenv: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux).
2. Install dependencies: `pip install -r requirements.txt`.
3. Update .env with your AWS/RDS details.
4. Run the app: `flask run` (set FLASK_APP=app/__init__.py if needed).
5. Access at http://127.0.0.1:5000/login.

## Deployment
Use Elastic Beanstalk (upload ZIP of project).

## Testing
Run `pytest` in terminal for test
