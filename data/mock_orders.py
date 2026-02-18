MOCK_ORDER_DB = {
    "ORD123": {
        "order_status": "In Transit",
        "delivery_date": None, # Rule: Don't guess if None
        "refund_eligible": False,
        "current_location": "Chicago Hub"
    },
    "ORD456": {
        "order_status": "Delivered",
        "delivery_date": "2024-05-10",
        "refund_eligible": True,
        "current_location": "Customer Doorstep"
    },
    "ORD789": {
        "order_status": "Delayed",
        "delivery_date": "2024-05-20",
        "refund_eligible": False,
        "current_location": "Unknown"
    }
}