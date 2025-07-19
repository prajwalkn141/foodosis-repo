from foodosis_aws_utils import rds_utils  # Reuse RDS connection from library

class Inventory:
    @staticmethod
    def add(name, quantity, unit, expiration_date, s3_file_key):
        return rds_utils.add_item(name, quantity, unit, expiration_date, s3_file_key)

    @staticmethod
    def get_all():
        return rds_utils.get_items()

    @staticmethod
    def update(item_id, name, quantity, unit, expiration_date):
        rds_utils.update_item(item_id, name, quantity, unit, expiration_date)

class Admin:
    @staticmethod
    def validate(username, password):
        return rds_utils.validate_user(username, password)