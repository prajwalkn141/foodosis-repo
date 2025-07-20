# test_food_safety_lib.py
# Test script for our custom food safety library

from datetime import datetime, timedelta
from food_safety_lib import (
    calculate_shelf_life,
    get_expiry_status,
    get_safety_score,
    categorize_risk_level,
    generate_alert_message,
    get_recommended_storage
)

print("=== Testing Food Safety Library ===\n")

# Test 1: Shelf Life Calculation
print("1. Testing Shelf Life Calculation:")
products = ['milk', 'chicken', 'bread', 'apples', 'canned beans']
for product in products:
    shelf_life = calculate_shelf_life(product)
    print(f"   {product}: {shelf_life} days")

# Test 2: Expiry Status
print("\n2. Testing Expiry Status:")
test_dates = [
    (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),  # Expired
    (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),  # Tomorrow
    (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),  # 5 days
    (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'), # 10 days
    (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'), # 30 days
]

for date in test_dates:
    status, emoji, days = get_expiry_status(date)
    print(f"   {date}: {emoji} {status} ({days} days)")

# Test 3: Safety Score
print("\n3. Testing Safety Score:")
test_item = {
    'name': 'Test Milk',
    'expiration_date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
    'quantity': 50
}

safety_info = get_safety_score(test_item['expiration_date'], test_item['quantity'])
print(f"   Item: {test_item['name']}")
print(f"   Safety Score: {safety_info['score']}/100")
print(f"   Risk Level: {safety_info['risk_level']}")
print(f"   Recommendations:")
for rec in safety_info['recommendations']:
    print(f"     - {rec}")

# Test 4: Alert Message Generation
print("\n4. Testing Alert Message Generation:")
alert_msg = generate_alert_message(
    'Test Product',
    (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
    100,
    'kg'
)
print(alert_msg)

# Test 5: Storage Recommendations
print("\n5. Testing Storage Recommendations:")
categories = ['dairy', 'meat', 'vegetables']
for category in categories:
    storage = get_recommended_storage(category)
    print(f"\n   {category.upper()}:")
    print(f"     Temperature: {storage['temperature']}")
    print(f"     Location: {storage['location']}")
    print(f"     Tips: {storage['tips']}")

print("\n✅ Food Safety Library tests completed!")