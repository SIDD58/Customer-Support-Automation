from data.mock_orders import MOCK_ORDER_DB
from customer_pipeline.state import State
from typing import Dict, Any


def fetch_order_context_node(state: State)-> Dict[str, Any]:
    order_id = state.get("order_id")
    order_info = MOCK_ORDER_DB.get(order_id)
    
    if not order_info:
        # Handle missing order
        return {
            "order_status": "Not Found",
            "delivery_date": None,
            "refund_eligible": None,
            "internal_logs": [f"Error: Order {order_id} not found in DB."]
        }
    
    # Update state with found data
    return {
        "order_status": order_info["order_status"],
        "delivery_date": order_info["delivery_date"],
        "refund_eligible": order_info["refund_eligible"],
        "internal_logs": [f"Successfully fetched context for {order_id}."]
    }