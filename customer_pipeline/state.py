from typing import Optional, TypedDict, Annotated
import operator
class State(TypedDict):
    # Input from the customer
    customer_message: str
    order_id: str

    # Context from mock data Flattened and message category
    order_status: str       
    delivery_date: Optional[str] 
    refund_eligible: bool
    message_category: str

    #validation logic 
    is_compliant: bool
    compliance_feedback: str
    retry_count: int  # Track nummber of times we loop for compliance fixes

    # ai_response fields
    draft_response: str
    final_response: str

    #debugging fields
    internal_logs: Annotated[list[str], operator.add]