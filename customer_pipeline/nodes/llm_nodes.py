from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from customer_pipeline.state import State
from customer_pipeline.pipeline_schemas.category_response import CategoryResponse
from customer_pipeline.pipeline_schemas.compliance_check_schema import ComplianceCheck
from dotenv import load_dotenv

load_dotenv()  # Load open ai key from .env file

# Initialize our LLM client
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def categorize_message_node(state: State):
    # Structured LLM
    structured_llm = llm.with_structured_output(CategoryResponse)
    
    # System Instructions
    system_instructions = (
        "You are a professional triage agent for an e-commerce platform. "
        "Your task is to categorize the user's message into EXACTLY one category based on these rules:\n\n"
        "- SHIPPING: Use for inquiries about order location, tracking numbers, or delivery dates.\n"
        "- REFUND: Use for inquiries about money back, returns, or order cancellations.\n"
        "- GENERAL: Use for greetings, feedback, or issues not related to a specific order status.\n\n"
        "Return ONLY the structured data. Do not engage in conversation."
    )
    # Exectuion with error handling for guardrails
    try:
        structured_result = structured_llm.invoke([
            SystemMessage(content=system_instructions),
            HumanMessage(content=f"Message: {state['customer_message']}")
        ])
        
        return {
            "message_category": structured_result.category,
            "internal_logs": [f"Categorized as {structured_result.category}. Reason: {structured_result.reasoning}"]
        }
    # LLM times out or the parsing fails, we default to GENERAL
    except Exception as e:
        return {
            "message_category": "GENERAL",
            "internal_logs": [f"CRITICAL: Categorization failed with error: {str(e)}. Defaulted to GENERAL."]
        }


######################################################################################
#####################################################################################


def drafting_node(state: State):
    # 1. Access the current retry count (default to 0)
    current_retries = state.get("retry_count", 0)
    
    # 2. Build the Feedback Context (only if a previous attempt failed)
    feedback_context = ""
    if state.get("compliance_feedback") and state.get("draft_response"):
        feedback_context = f"""
        ---
        PREVIOUS ATTEMPT: {state['draft_response']}
        REJECTION REASON: {state['compliance_feedback']}
        INSTRUCTION: Fix the draft to comply with business rules.
        ---
        """

    # 3. Context Summary with strict field handling
    context_summary = f"""
    CUSTOMER MESSAGE: {state['customer_message']}
    CATEGORY: {state['message_category']}
    ORDER STATUS: {state['order_status']}
    DELIVERY DATE: {state.get('delivery_date') or 'NOT AVAILABLE'}
    REFUND ELIGIBLE: {state.get('refund_eligible')}
    {feedback_context}
    """

    # 4. Strict System Instructions
    system_instructions = (
        "You are a professional customer support agent. Write a POLITE and CONCISE response.\n"
        "RULES:\n"
        "1. Use the provided ORDER STATUS to inform the customer.\n"
        "2. DO NOT promise a specific delivery date if it is 'NOT AVAILABLE'.\n"
        "3. DO NOT promise a refund if 'REFUND ELIGIBLE' is False or None.\n"
        "4. Be empathetic but do not make financial commitments or guarantees.\n"
        "5. If information is missing (None/NOT AVAILABLE), tell the customer we are investigating or remain silent on that specific point."
    )

    # 5. Generate the Response
    response = llm.invoke([
        SystemMessage(content=system_instructions),
        HumanMessage(content=f"Context and History:\n{context_summary}\n\nDraft the response:")
    ])

    # 6. Return the updated state (Increment retry_count here)
    return {
        "draft_response": response.content,
        "retry_count": current_retries + 1,
        "internal_logs": [f"Draft attempt #{current_retries + 1} generated."]
    }


#####################################################################################
####################################################################################



def compliance_guardrail_node(state: State):
    structured_llm = llm.with_structured_output(ComplianceCheck)
    
    audit_prompt = f"""
    Review this support draft for business violations.

    CRITICAL BUSINESS RULES:
    1. REFUND RULE:
       - ONLY apply this rule if the Category is 'REFUND' or the draft mentions refunds/money
       - If Refund Eligible is 'True': The draft MAY confirm a refund.
       - If Refund Eligible is 'False': The draft MUST NOT promise a refund. It should politely decline or explain policy.
       - If Refund Eligible is 'None': The draft MUST NOT confirm OR deny a refund. It should state information is unavailable.
    
    2. DELIVERY RULE:
       - ONLY apply this rule if the Category is 'SHIPPING' or the draft mentions soemthing about delivery dates
       - If Delivery Date is 'None' or 'NOT AVAILABLE': The draft MUST NOT mention any specific dates, days of the week, or timeframes (e.g., 'in 3 days').

    
    DATA:
    - Refund Eligible: {state['refund_eligible']}
    - Delivery Date: {state['delivery_date']}
    
    DRAFT TO AUDIT:
    "{state['draft_response']}"

    Does this draft violate any of the rules above? If so, specify which one and why.
    """
    
    audit_result = structured_llm.invoke([SystemMessage(content=audit_prompt)])
    
    # If compliant, we can move draft to final_response
    updates = {
        "is_compliant": audit_result.is_compliant,
        "compliance_feedback": audit_result.feedback,
        "internal_logs": [f"Compliance Check: {audit_result.is_compliant}"]
    }
    
    if audit_result.is_compliant:
        updates["final_response"] = state["draft_response"]
        
    return updates