from flask import request, session, render_template, redirect, url_for, flash
from app import app
from foodosis_aws_utils import rds_utils, s3_utils, cloudwatch_utils, auth_utils, lambda_utils  # Using lambda_utils
from dotenv import load_dotenv
import os
<<<<<<< HEAD
import boto3
from datetime import datetime, timedelta # Added for date calculations
import json # Added for JSON payload
from food_safety_lib import get_expiry_status, get_safety_score, calculate_shelf_life, generate_alert_message


=======
from datetime import datetime, timedelta
import json
>>>>>>> 19524b18a22413522dc1aa6aa94bcb2d837b35b4

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



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if not username.endswith('@gmail.com'):
            flash('Email must end with @gmail.com', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('signup.html')
        
        # Check if user already exists
        if rds_utils.user_exists(username):
            flash('User already exists with this email', 'error')
            return render_template('signup.html')
        
        # Create new user with properly hashed password
        success = rds_utils.create_user(username, password)
        
        if success:
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error creating account. Please try again.', 'error')
            return render_template('signup.html')
    
    return render_template('signup.html')



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
    if request.method == 'POST':
        name = request.form['name']
        try:
            quantity = float(request.form['quantity'])
        except ValueError as e:
<<<<<<< HEAD
            print(f"Error: Invalid quantity - {e}")
=======
            print(f"Error: Invalid quantity - {e}")  # Debug print
>>>>>>> 19524b18a22413522dc1aa6aa94bcb2d837b35b4
            flash(f"Invalid quantity: {str(e)}", 'error')
            return render_template('add_update_item.html', action='add', error=f"Invalid quantity: {str(e)}")
        
        unit = request.form['unit']
        expiration_date_str = request.form.get('expiration_date')
        file = request.files.get('file')
        s3_file_key = None

        # NEW: Use food_safety_lib to calculate shelf life
        if not expiration_date_str:
            # If no expiration date provided, calculate based on product type
            shelf_life_days = calculate_shelf_life(name)
            suggested_expiry = (datetime.now() + timedelta(days=shelf_life_days)).strftime('%Y-%m-%d')
            flash(f"💡 Tip: Based on the product type, suggested expiration date is {suggested_expiry} ({shelf_life_days} days)", 'info')

        # Load fresh credentials for S3
        load_dotenv()
        fresh_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        fresh_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        fresh_session_token = os.getenv('AWS_SESSION_TOKEN')
        fresh_region = os.getenv('AWS_REGION', 'us-east-1')
        fresh_s3_bucket = os.getenv('S3_BUCKET')

<<<<<<< HEAD
        if file and file.filename:
            try:
                if not fresh_s3_bucket:
                    print("Error: S3_BUCKET environment variable not set.")
=======
        print(f"Loaded AWS_ACCESS_KEY_ID: {fresh_access_key}")  # Debug print
        print(f"Loaded S3_BUCKET: {fresh_s3_bucket}")  # Debug print

        if file and file.filename:
            try:
                if not fresh_s3_bucket:
                    print("Error: S3_BUCKET environment variable not set.")  # Debug print
>>>>>>> 19524b18a22413522dc1aa6aa94bcb2d837b35b4
                    flash("S3 bucket not configured. Please check your .env file.", 'error')
                    return render_template('add_update_item.html', action='add', error="S3 bucket not configured.")

                key = f"inventory/{name.replace(' ', '_')}_{file.filename}"
                s3_utils.update_s3_client(fresh_access_key, fresh_secret_key, fresh_session_token, fresh_region)
<<<<<<< HEAD
                s3_file_key = s3_utils.upload_file(file, key)
                print(f"S3 upload successful. Key: {s3_file_key}")

            except Exception as e:
                print(f"Error: S3 upload failed - {e}")
                flash(f"S3 upload failed: {str(e)}", 'error')
                return render_template('add_update_item.html', action='add', error=f"S3 upload failed: {str(e)}")

        item_id = None
        try:
            item_id = rds_utils.add_item(name, quantity, unit, expiration_date_str, s3_file_key)
            flash('Item added successfully!', 'success')

            # NEW: Use food_safety_lib for safety analysis
            if expiration_date_str:
                # Get expiry status
                status, emoji, days_remaining = get_expiry_status(expiration_date_str)
                
                # Get safety score
                safety_info = get_safety_score(expiration_date_str, quantity)
                
                # Display safety information
                flash(f"{emoji} Expiry Status: {status} - {days_remaining} days remaining", 'info')
                flash(f"🛡️ Safety Score: {safety_info['score']}/100 - Risk Level: {safety_info['risk_level']}", 'info')
                
                # Show recommendations
                for rec in safety_info['recommendations']:
                    flash(rec, 'warning')
                
                # Check for immediate expiry and invoke Lambda
                if days_remaining <= 7:
                    print(f"Item '{name}' (ID: {item_id}) expires in {days_remaining} days. Invoking Lambda.")
                    
                    lambda_client = boto3.client(
                        'lambda',
                        aws_access_key_id=fresh_access_key,
                        aws_secret_access_key=fresh_secret_key,
                        aws_session_token=fresh_session_token,
                        region_name=fresh_region
                    )
                    
                    payload = {"item_id": item_id}
                    
                    try:
                        response = lambda_client.invoke(
                            FunctionName='foodosis-expiration-check-lambda',
                            InvocationType='Event',
                            Payload=json.dumps(payload)
                        )
                        if response.get('StatusCode') == 202:
                            # Generate detailed alert message using the library
                            alert_msg = generate_alert_message(name, expiration_date_str, quantity, unit)
                            print(f"Alert message: {alert_msg}")
                            flash("📧 Email notification triggered for expiring item!", 'info')
                        else:
                            flash("Failed to trigger email notification.", 'warning')
                    except Exception as lambda_e:
                        print(f"Error invoking Lambda: {lambda_e}")
                        flash(f"Error triggering notification: {str(lambda_e)}", 'error')
=======

                print(f"Attempting S3 upload for key: {key}")  # Debug print
                s3_file_key = s3_utils.upload_file(file, key)
                print(f"S3 upload successful. Key: {s3_file_key}")  # Debug print

            except Exception as e:
                print(f"Error: S3 upload failed - {e}")  # Debug print
                flash(f"S3 upload failed: {str(e)}", 'error')
                return render_template('add_update_item.html', action='add', error=f"S3 upload failed: {str(e)}")
        else:
            print("No file provided for upload.")  # Debug print

        item_id = None  # Initialize item_id
        try:
            print(f"Attempting to add item to RDS: Name={name}, Quantity={quantity}, Unit={unit}, Expiration={expiration_date_str}, S3_Key={s3_file_key}")  # Debug print
            item_id = rds_utils.add_item(name, quantity, unit, expiration_date_str, s3_file_key)
            print(f"Item added to RDS successfully. Item ID: {item_id}")  # Debug print
            flash('Item added successfully!', 'success')

            # Check for immediate expiry and invoke Lambda using lambda_utils
            if expiration_date_str:
                expiration_date_obj = datetime.strptime(expiration_date_str, '%Y-%m-%d')
                creation_date = datetime.now().date()  # Approximate creation date
                days_until_expiry = (expiration_date_obj.date() - creation_date).days
                
                if days_until_expiry <= 7:  # Threshold of 7 days inclusive
                    print(f"Item '{name}' (ID: {item_id}) expires in {days_until_expiry} days. Invoking Lambda for immediate check.")
                    
                    payload = {
                        "item_id": item_id,
                        "name": name,
                        "expiration_date": expiration_date_str,
                        "days_until_expiry": days_until_expiry
                    }
                    
                    try:
                        response = lambda_utils.invoke_lambda('foodosis-expiration-check-lambda', payload, fresh_region)  # Corrected function name
                        print(f"Lambda invocation response: {response}")
                        if response.get('StatusCode') == 202:
                            flash("Immediate expiry check triggered successfully!", 'info')
                        else:
                            flash("Failed to trigger immediate expiry check. Check Lambda logs.", 'warning')
                    except Exception as lambda_e:
                        print(f"Error invoking Lambda for immediate check: {lambda_e}")
                        flash(f"Error triggering immediate expiry check: {str(lambda_e)}", 'error')
                else:
                    print(f"Item '{name}' (ID: {item_id}) expires in {days_until_expiry} days. No immediate check needed.")
>>>>>>> 19524b18a22413522dc1aa6aa94bcb2d837b35b4

            return redirect(url_for('dashboard'))

        except Exception as e:
<<<<<<< HEAD
            print(f"Error: Database error - {e}")
=======
            print(f"Error: Database error - {e}")  # Debug print
>>>>>>> 19524b18a22413522dc1aa6aa94bcb2d837b35b4
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
<<<<<<< HEAD
    return redirect(url_for('login'))

@app.route('/safety_dashboard')
def safety_dashboard():
    """Food safety dashboard using our custom library"""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Import our custom library
    from food_safety_lib import get_batch_alerts, get_safety_score, calculate_waste_cost
    
    # Get all inventory items
    items = rds_utils.get_items()
    
    # Process alerts using our library
    alerts = get_batch_alerts(items)
    
    # Calculate safety scores for all items
    safety_analysis = []
    total_potential_waste = 0.0
    
    for item in items:
        if item.get('expiration_date'):
            # Get safety score
            safety_info = get_safety_score(
                str(item['expiration_date']), 
                item.get('quantity', 0)
            )
            
            # Calculate potential waste (assuming $10 per unit for demo)
            waste_cost = calculate_waste_cost(
                item.get('quantity', 0),
                10.0,  # Unit cost
                str(item['expiration_date'])
            )
            
            total_potential_waste += waste_cost
            
            safety_analysis.append({
                'item': item,
                'safety_score': safety_info['score'],
                'risk_level': safety_info['risk_level'],
                'risk_color': safety_info['risk_color'],
                'recommendations': safety_info['recommendations'],
                'potential_waste_cost': waste_cost
            })
    
    # Sort by safety score (lowest first - highest risk)
    safety_analysis.sort(key=lambda x: x['safety_score'])
    
    # Count items by category
    alert_counts = {
        'expired': len(alerts['expired']),
        'critical': len(alerts['critical']),
        'warning': len(alerts['warning']),
        'caution': len(alerts['caution']),
        'normal': len(alerts['normal'])
    }
    
    return render_template('safety_dashboard.html',
        alerts=alerts,
        alert_counts=alert_counts,
        safety_analysis=safety_analysis[:10],  # Top 10 risky items
        total_potential_waste=total_potential_waste
    )
=======
    return redirect(url_for('login'))
>>>>>>> 19524b18a22413522dc1aa6aa94bcb2d837b35b4
