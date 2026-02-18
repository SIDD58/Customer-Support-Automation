
from celery import Celery
from customer_pipeline.workflow import app as langgraph_app

# Point to the Persistent Redis (Port 6379)
celery_app = Celery(
    "support_tasks", 
    broker="redis://localhost:6379/0", 
    backend="redis://localhost:6379/0"
)

@celery_app.task(name="process_support_message", bind=True)
def run_support_workflow(self:Task, inquiry: dict):
    # Prepare input for LangGraph
    initial_state = {
        "customer_message": inquiry["customer_message"],
        "order_id": inquiry["order_id"],
        "retry_count": 0,
        "internal_logs": [f"Task {self.request.id} started."]
    }
    
    # Invoke the compiled pipeline
    final_result = langgraph_app.invoke(initial_state)
    
    # Return specific fields for the API to fetch later
    return {
            "task_id": self.request.id,
            "status": "completed",
            "category": final_result.get("message_category"),
            "final_response": final_result.get("final_response"),
            "compliance_checked": final_result.get("is_compliant"),
            "logs": final_result.get("internal_logs")
        }