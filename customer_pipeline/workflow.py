from langgraph.graph import StateGraph,START,END
from data.mock_orders import MOCK_ORDER_DB
from customer_pipeline.state import State
from customer_pipeline.nodes.utility_nodes import fetch_order_context_node,fallback_node
from customer_pipeline.nodes.llm_nodes import categorize_message_node, drafting_node, compliance_guardrail_node


def check_compliance_gate(state: State):
    # If guardrail passed
    if state["is_compliant"]:
        return "approved"
    
    # If failed 3 times
    if state.get("retry_count", 0) >= 3:
        return "max_retries_exceeded"
    
    # else we retry
    return "retry"


graph = StateGraph(State)
print("Graph Nodes:")
graph.add_node("fetch_context", fetch_order_context_node)
graph.add_node("categorize", categorize_message_node)
graph.add_node("drafter", drafting_node)
graph.add_node("guardrail", compliance_guardrail_node)
graph.add_node("fallback_node", fallback_node)


graph.add_edge(START, "fetch_context")
graph.add_edge("fetch_context", "categorize")
graph.add_edge("categorize", "drafter")
graph.add_edge("drafter", "guardrail")

# CONDITIONAL LOGIC BASED ON COMPLIANCE CHECK
graph.add_conditional_edges(
"guardrail",
check_compliance_gate,
{
    "approved": END,
    "retry": "drafter", # Loop back to fix the draft
    "max_retries_exceeded": "fallback_node"
})
graph.add_edge("fallback_node", END)

app = graph.compile()
# final_state = app.invoke({'order_id': 'ORD123','customer_message': 'Where is my order?'})
# print("\nFinal State:", final_state)
    
if __name__ == "__main__":
    final_state = app.invoke({'order_id': 'ORD123','customer_message': 'Where is my order?'})
    print("\nFinal State:", final_state)


