from flask import request, session, render_template, redirect, url_for, flash
from app import app
from foodosis_aws_utils import rds_utils, s3_utils, cloudwatch_utils, auth_utils
from dotenv import load_dotenv
import os
import boto3
from datetime import datetime, timedelta # Added for date calculations
import json # Added for JSON payload

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if auth_utils.validate_user(username, password):
            session['logged_in'] = True
            session['username'] = username
            # cloudwatch_utils.put_log_event(f"User {username} logged in successfully")  # Temporarily disabled
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password, or email must end with @gmail.com", 'error')
            return render_template('login.html', error="Invalid username or password, or email must end with @gmail.com")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    items = rds_utils.get_items()
    for item in items:
        if item['s3_file_key']:
            item['file_url'] = s3_utils.get_file_url(item['s3_file_key'])
    low_stock_count = len(rds_utils.get_low_stock_items())
    expiring_count = len(rds_utils.get_expiring_items())
    return render_template('dashboard.html', items=items, low_stock_count=low_stock_count, expiring_count=expiring_count)

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    # if not session.get('logged_in'):  # Temporarily omitted for testing
    #     return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        try:
            quantity = float(request.form['quantity'])
        except ValueError as e:
            print(f"Error: Invalid quantity - {e}") # Debug print
            flash(f"Invalid quantity: {str(e)}", 'error')
            return render_template('add_update_item.html', action='add', error=f"Invalid quantity: {str(e)}")
        unit = request.form['unit']
        expiration_date_str = request.form.get('expiration_date')
        file = request.files.get('file')
        s3_file_key = None

        # Always load fresh credentials from .env for the S3 client to be updated
        load_dotenv()
        fresh_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        fresh_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        fresh_session_token = os.getenv('AWS_SESSION_TOKEN')
        fresh_region = os.getenv('AWS_REGION', 'us-east-1')
        fresh_s3_bucket = os.getenv('S3_BUCKET')

        print(f"Loaded AWS_ACCESS_KEY_ID: {fresh_access_key}") # Debug print
        print(f"Loaded S3_BUCKET: {fresh_s3_bucket}") # Debug print

        if file and file.filename:
            try:
                if not fresh_s3_bucket:
                    print("Error: S3_BUCKET environment variable not set.") # Debug print
                    flash("S3 bucket not configured. Please check your .env file.", 'error')
                    return render_template('add_update_item.html', action='add', error="S3 bucket not configured. Please check your .env file.")

                key = f"inventory/{name.replace(' ', '_')}_{file.filename}"

                s3_utils.update_s3_client(fresh_access_key, fresh_secret_key, fresh_session_token, fresh_region)

                print(f"Attempting S3 upload for key: {key}") # Debug print
                s3_file_key = s3_utils.upload_file(file, key)
                print(f"S3 upload successful. Key: {s3_file_key}") # Debug print

            except Exception as e:
                print(f"Error: S3 upload failed - {e}") # Debug print
                flash(f"S3 upload failed: {str(e)}", 'error')
                return render_template('add_update_item.html', action='add', error=f"S3 upload failed: {str(e)}")
        else:
            print("No file provided for upload.") # Debug print

        item_id = None # Initialize item_id
        try:
            print(f"Attempting to add item to RDS: Name={name}, Quantity={quantity}, Unit={unit}, Expiration={expiration_date_str}, S3_Key={s3_file_key}") # Debug print
            item_id = rds_utils.add_item(name, quantity, unit, expiration_date_str, s3_file_key)
            print(f"Item added to RDS successfully. Item ID: {item_id}") # Debug print
            flash('Item added successfully!', 'success')

            # --- NEW: Check for immediate expiry and invoke Lambda ---
            if expiration_date_str:
                try:
                    expiration_date_obj = datetime.strptime(expiration_date_str, '%Y-%m-%d')
                    days_until_expiry = (expiration_date_obj.date() - datetime.now().date()).days
                    
                    if days_until_expiry <= 7:
                        print(f"Item '{name}' (ID: {item_id}) expires in {days_until_expiry} days. Invoking Lambda for immediate check.")
                        
                        # Initialize Lambda client using Flask app's credentials
                        lambda_client = boto3.client(
                            'lambda',
                            aws_access_key_id=fresh_access_key,
                            aws_secret_access_key=fresh_secret_key,
                            aws_session_token=fresh_session_token,
                            region_name=fresh_region
                        )
                        
                        # Payload for the Lambda function
                        payload = {"item_id": item_id}
                        
                        try:
                            response = lambda_client.invoke(
                                FunctionName='foodosis-expiration-check-lambda', # Make sure this matches your Lambda function name
                                InvocationType='Event', # 'Event' for asynchronous invocation (don't wait for response)
                                Payload=json.dumps(payload)
                            )
                            print(f"Lambda invocation response: {response}")
                            if response.get('StatusCode') == 202: # 202 is for successful asynchronous invocation
                                flash("Immediate expiry check triggered successfully!", 'info')
                            else:
                                flash("Failed to trigger immediate expiry check. Check Lambda logs.", 'warning')
                        except Exception as lambda_e:
                            print(f"Error invoking Lambda for immediate check: {lambda_e}")
                            flash(f"Error triggering immediate expiry check: {str(lambda_e)}", 'error')
                    else:
                        print(f"Item '{name}' (ID: {item_id}) expires in {days_until_expiry} days. No immediate check needed.")

                except ValueError:
                    print(f"Warning: Could not parse expiration date '{expiration_date_str}' for immediate check.")
                except Exception as date_e:
                    print(f"Unexpected error during date calculation for immediate check: {date_e}")
            # --- END NEW: Check for immediate expiry and invoke Lambda ---

            return redirect(url_for('dashboard'))

        except Exception as e:
            print(f"Error: Database error - {e}") # Debug print
            flash(f"Database error: {str(e)}", 'error')
            return render_template('add_update_item.html', action='add', error=f"Database error: {str(e)}")
    
    return render_template('add_update_item.html', action='add')

@app.route('/update_item/<int:item_id>', methods=['GET', 'POST'])
def update_item(item_id):
    # if not session.get('logged_in'):  # Temporarily omitted for testing
    #     return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        try:
            quantity = float(request.form['quantity'])
        except ValueError:
            flash("Invalid quantity format", 'error')
            return render_template('add_update_item.html', action='update', item={'id': item_id}, error="Invalid quantity format")
        unit = request.form['unit']
        expiration_date = request.form.get('expiration_date')
        rds_utils.update_item(item_id, name, quantity, unit, expiration_date)
        # cloudwatch_utils.put_log_event(f"Updated item ID {item_id}")  # Temporarily disabled
        flash('Item updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    item = next((i for i in rds_utils.get_items() if i['id'] == item_id), None)
    if item is None:
        flash('Item not found!', 'error')
        return "Item not found", 404
    return render_template('add_update_item.html', action='update', item=item)

@app.route('/delete_item/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    # if not session.get('logged_in'): # Temporarily omitted for testing
    #     return redirect(url_for('login'))
    
    item_to_delete = None
    all_items = rds_utils.get_items()
    for item in all_items:
        if item['id'] == item_id:
            item_to_delete = item
            break

    if item_to_delete:
        s3_file_key = item_to_delete.get('s3_file_key')

        load_dotenv()
        fresh_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        fresh_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        fresh_session_token = os.getenv('AWS_SESSION_TOKEN')
        fresh_region = os.getenv('AWS_REGION', 'us-east-1')

        try:
            s3_utils.update_s3_client(fresh_access_key, fresh_secret_key, fresh_session_token, fresh_region)

            if s3_file_key:
                print(f"Attempting to delete S3 file: {s3_file_key}")
                s3_utils.delete_file(s3_file_key)
                print(f"S3 file {s3_file_key} deleted successfully.")
            else:
                print(f"No S3 file associated with item ID {item_id}.")

            rds_utils.delete_item(item_id)
            print(f"Item ID {item_id} deleted from database successfully.")
            flash(f'Item "{item_to_delete.get("name", "Unknown Item")}" deleted successfully!', 'success')
            return redirect(url_for('dashboard'))

        except Exception as e:
            print(f"Error during deletion of item ID {item_id}: {e}")
            flash(f'Error deleting item: {str(e)}', 'error')
            return redirect(url_for('dashboard'))
    else:
        print(f"Item with ID {item_id} not found for deletion.")
        flash('Item not found for deletion.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))
