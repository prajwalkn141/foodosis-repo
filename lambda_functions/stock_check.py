from foodosis_aws_utils import rds_utils, sns_utils, cloudwatch_utils

def handler(event, context):
    try:
        low_stock_items = rds_utils.get_low_stock_items()
        if low_stock_items:
            message = "Low stock alert:\n"
            for item in low_stock_items:
                message += f"Item '{item['name']}' has only {item['quantity']} {item['unit']} left.\n"
            sns_utils.publish_notification(message)
            cloudwatch_utils.put_log_event("Low stock notification sent")
        return {'statusCode': 200, 'body': 'Stock check complete'}
    except Exception as e:
        cloudwatch_utils.put_log_event(f"Stock check error: {e}")
        return {'statusCode': 500, 'body': 'Stock check failed'}