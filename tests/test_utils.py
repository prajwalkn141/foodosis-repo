import pytest
from foodosis_aws_utils import rds_utils, s3_utils

def test_get_connection():
    conn = rds_utils.get_connection()
    assert conn.is_connected() == True
    conn.close()

def test_add_item():
    item_id = rds_utils.add_item('Test Item', 100.0, 'kg', None, None)
    assert item_id > 0

# Add more tests as needed, e.g., for s3_utils
def test_get_file_url():
    url = s3_utils.get_file_url('test_key')
    assert url.startswith('https://')