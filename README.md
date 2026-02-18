# AI Customer Support Automation (Async Pipeline)

A production-grade backend system that uses **LangGraph** for multi-step AI reasoning and **Celery/Redis** for asynchronous background processing.

## Key Features
- **Async Architecture**: Immediate `202 Processing` response while the AI works in the background (celery redis queue)
- **Categorizer**: Categorize the message , retry Logic and fallback node. 
- **Compliance Guardrails**: A self-correcting loop that audits AI drafts against business rules (no fake dates, no unauthorized refunds). 
- **Stateful Reasoning**: Uses LangGraph to maintain context, retry counts, and internal logs.
- **Observability**: Integrated monitoring via langsmith (form iterative prompt development) , Flower (Celery) and RedisInsight
---

## 🛠 Prerequisites

Ensure you have the following installed:
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Docker & Docker Compose](https://www.docker.com/products/docker-desktop/)
- An **OpenAI API Key**
- Use any Tool for API testing like Postman 

---

## Environment Setup

Create a `.env` file in the root directory:

```env
# AI Provider
OPENAI_API_KEY=sk-proj-your-key-here

# LangSmith (Highly Recommended for visualizing the Graph)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_your_key_here
LANGCHAIN_PROJECT="support-automation-async"

# Redis Config
REDIS_PERSISTENT_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6380/0
```

## Setup Commands (Run each command in different terminal in same order)
1. docker-compose up -d
2. uv sync
3. uv run celery -A tasks.pipeline_task:celery_app worker --loglevel=info --pool=solo
4. uv run uvicorn main:app --reload

## FAST API request and response 
Use something like Postman to Test URL 

1) POST http://localhost:8000/support/reply
{
   "order_id": "ORD123",
   "customer_message": "Where is my order? It’s been 5 days."
}

Response {"status": "processing", "task_id": "uuid-string"}

2) GET http://localhost:8000/support/status/{task_id}

Response 
{
  "status": "completed",
  "result": {
    "category": "SHIPPING",
    "final_response": "I see your order ORD123 is currently In Transit...",
    "compliance_checked": true
  }
}

## Project Structure
```
.
├── customer_pipeline/
│   ├── nodes/           # LangGraph Node logic (Categorizer, Drafter, etc.)
│   ├── state.py         # TypedDict State definition
│   └── workflow.py      # Graph construction and compilation
├── tasks/               # Celery task definitions
├── main.py              # FastAPI routes
├── docker-compose.yml   # Redis services & Celery and redis Monitoring setup
└── pyproject.toml       # Dependencies (uv)
```


## DEBUGGING TOOLS AND VISUALIZATIONS

FastAPI Docs
http://localhost:8000/docs,
Test the API endpoints (Swagger UI).

Flower
"Monitor Celery tasks, success rates, and retries."
http://localhost:5555,

RedisInsight 
"Inspect Redis databases (Port 6379 for Queue, 6380 for Cache)."
http://localhost:5540,

Click on Connect existing database 
Add connection URL ->redis://default@redis-db:6379
Then Add connection URL ->redis://default@redis-cache:6379


LangSmith,
View the step-by-step node execution of your AI pipeline.
smith.langchain.com

## Bussiness Rules 
No Hallucinated Dates: If delivery_date is None, AI is forbidden from giving a timeframe.

Refund Integrity: If refund_eligible is False, AI must politely decline.

Loop Limitation: The system allows a maximum of 3 retries for the AI to fix a non-compliant draft before escalating to a human fallback message.


## AI PIPELINE
![Demo Screenshot](images/flowchart.png)