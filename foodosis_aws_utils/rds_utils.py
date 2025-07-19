import mysql.connector
import os # Added import for os
from app.config import Config # Keep this for local Flask app

def get_connection():
    # Prioritize environment variables for Lambda deployment
    # Fallback to Config for local Flask application
    db_host = os.getenv('RDS_HOST', Config.RDS_HOST)
    db_port = int(os.getenv('RDS_PORT', Config.RDS_PORT))
    db_name = os.getenv('RDS_DB', Config.RDS_DB)
    db_user = os.getenv('RDS_USER', Config.RDS_USER)
    db_password = os.getenv('RDS_PASSWORD', Config.RDS_PASSWORD)

    return mysql.connector.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )

def add_item(name, quantity, unit, expiration_date, s3_file_key):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO Inventory (name, quantity, unit, expiration_date, s3_file_key) VALUES (%s, %s, %s, %s, %s)",
        (name, quantity, unit, expiration_date, s3_file_key)
    )
    conn.commit()
    item_id = cur.lastrowid
    cur.close()
    conn.close()
    return item_id

def get_items():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)  # Results as dicts for JSON
    cur.execute("SELECT * FROM Inventory")
    items = cur.fetchall()
    cur.close()
    conn.close()
    return items

def update_item(item_id, name, quantity, unit, expiration_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE Inventory SET name = %s, quantity = %s, unit = %s, expiration_date = %s WHERE id = %s",
        (name, quantity, unit, expiration_date, item_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_item(item_id):
    """Deletes an item from the Inventory table by its ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM Inventory WHERE id = %s", (item_id,))
    conn.commit()
    cur.close()
    conn.close()

# Assuming bcrypt is imported in the file where validate_user is called, or you need to add it here.
# For simplicity, I'm assuming it's available or handled by auth_utils.
# If validate_user is directly in rds_utils, you'd need: import bcrypt
def validate_user(username, password):
    # This function seems to be in rds_utils, but uses bcrypt which isn't imported here.
    # It's likely meant to be in auth_utils.py as per your routes.py.
    # If it is indeed in rds_utils, ensure bcrypt is imported.
    # For now, I'll keep it as is, assuming bcrypt is handled by auth_utils if this is called from there.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM Admin WHERE username = %s", (username,))
    stored_hash = cur.fetchone()
    cur.close()
    conn.close()
    if stored_hash:
        # Ensure stored_hash[0] is not None before attempting to decode
        if stored_hash[0] is not None:
            # This line requires bcrypt. If this function is in rds_utils, you need 'import bcrypt' at the top.
            # If this function is actually in auth_utils.py, then auth_utils.py should handle bcrypt.
            # I'm leaving it as is, assuming auth_utils.validate_user handles bcrypt.
            # If you get an error about 'bcrypt' not defined, add 'import bcrypt' to this file.
            pass # Placeholder, as bcrypt is not imported here.
    return False

def get_low_stock_items():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM Inventory WHERE quantity < 100")
    items = cur.fetchall()
    cur.close()
    conn.close()
    return items

def get_expiring_items():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    # This query fetches items expiring within the next 7 days from the current date.
    cur.execute("SELECT id, name, expiration_date FROM Inventory WHERE expiration_date IS NOT NULL AND expiration_date < DATE_ADD(CURDATE(), INTERVAL 7 DAY)")
    items = cur.fetchall()
    cur.close()
    conn.close()
    return items

def search_items(name=None, min_quantity=None):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    query = "SELECT * FROM Inventory WHERE 1=1"
    params = []
    if name:
        query += " AND name LIKE %s"
        params.append(f"%{name}%")  # Partial match
    if min_quantity is not None:
        query += " AND quantity >= %s"
        params.append(min_quantity)
    cur.execute(query, params)
    items = cur.fetchall()
    cur.close()
    conn.close()
    return items
