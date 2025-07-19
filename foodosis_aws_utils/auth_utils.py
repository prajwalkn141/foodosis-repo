from .rds_utils import get_connection

def validate_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM Admin WHERE username = %s", (username,))
    stored_data = cur.fetchone()
    cur.close()
    conn.close()
    if stored_data and stored_data[0] == password and username.endswith('@gmail.com'):
        return True
    return False