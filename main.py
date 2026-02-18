from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from tasks.pipeline_task import run_support_workflow
from celery.result import AsyncResult

app = FastAPI(title="AI Support Automation")

# --- Schemas ---
class SupportRequest(BaseModel):
    order_id: str
    customer_message: str

# --- Endpoints ---

@app.post("/support/reply")
async def create_support_task(request: SupportRequest):
    """
    Receives customer inquiry and triggers the Async LangGraph pipeline.
    Returns a task_id immediately.
    """
    # .delay() is a Celery method that sends the task to Redis
    task = run_support_workflow.delay(request.model_dump())
    
    return {
        "status": "processing",
        "task_id": task.id,
        "message": "AI is analyzing your order and drafting a response."
    }

@app.get("/support/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Checks if the AI has finished processing the message.
    """
    result = AsyncResult(task_id)
    
    # PENING
    if result.status == 'PENDING':
        return {"status": "processing"}
    
    # SUCCESS
    if result.status == 'SUCCESS':
        return {
            "status": "completed",
            "result": result.result
        }
    
    #FAILURE
    if result.status == 'FAILURE':
        return {
            "status": "failed",
            "error": str(result.info)
        }
    
    return {"status": result.status}