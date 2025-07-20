import mysql.connector
import os
import bcrypt

def get_connection():
    # Try to get from environment variables first (for Lambda and testing)
    db_host = os.getenv('RDS_HOST')
    db_port = os.getenv('RDS_PORT')
    db_name = os.getenv('RDS_DB')
    db_user = os.getenv('RDS_USER')
    db_password = os.getenv('RDS_PASSWORD')
    
    # If not in env, try to import from Config (for Flask app)
    if not all([db_host, db_port, db_name, db_user, db_password]):
        try:
            from app.config import Config
            db_host = db_host or Config.RDS_HOST
            db_port = db_port or Config.RDS_PORT
            db_name = db_name or Config.RDS_DB
            db_user = db_user or Config.RDS_USER
            db_password = db_password or Config.RDS_PASSWORD
        except ImportError:
            # If we can't import Config, environment variables must be set
            raise ValueError("Database configuration not found. Set environment variables or ensure app.config is available.")
    
    return mysql.connector.connect(
        host=db_host,
        port=int(db_port),
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
    cur = conn.cursor(dictionary=True)
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
        params.append(f"%{name}%")
    if min_quantity is not None:
        query += " AND quantity >= %s"
        params.append(min_quantity)
    cur.execute(query, params)
    items = cur.fetchall()
    cur.close()
    conn.close()
    return items

def user_exists(username):
    """Check if a user already exists in the database"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM Admin WHERE username = %s", (username,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count > 0

def create_user(username, password):
    """Create a new user with hashed password"""
    try:
        # Generate salt and hash the password
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Admin (username, password_hash) VALUES (%s, %s)",
            (username, hashed_password.decode('utf-8'))
        )
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def validate_user_secure(username, password):
    """Validate user with proper password hashing"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM Admin WHERE username = %s", (username,))
    stored_data = cur.fetchone()
    cur.close()
    conn.close()
    
    if stored_data and stored_data[0]:
        # Check if the password is hashed (bcrypt hashes start with $2b$)
        stored_password = stored_data[0]
        if stored_password.startswith('$2b$'):
            # It's a bcrypt hash, verify properly
            return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
        else:
            # Legacy plain text password (for backward compatibility)
            return stored_password == password
    return False