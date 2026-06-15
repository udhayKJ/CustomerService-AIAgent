from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

import main
from main import validate_input, InputGuardrail, mainAgent, validate_output
import observability as obs

class QueryRequest(BaseModel):
    question: str

app = FastAPI(title="Customer Support Agent")

#GET /health

@app.post("/query")
def query(request: QueryRequest):
    main.init_metrics()
    question = request.question
    blocked_input = False
    answer = ""
    if not validate_input(question):
        response = InputGuardrail(question)
        if "unsafe" in response.strip().lower():
            blocked_input = True
            answer = "I cannot assist with that request. Please contact official support."
        else:
            answer = mainAgent(question)
            answer = validate_output(answer)
    else:
        answer = mainAgent(question)
        answer = validate_output(answer)
    
    metrics = main.get_metrics()
    obs.log(
        request_id=str(uuid.uuid4()),
        question=question,
        latency={
            "IG_latency": metrics["IG_latency"],
            "Response_latency": metrics["request_latency"],
            "Total_latency": metrics["IG_latency"] + metrics["retrieval_latency"] + metrics["request_latency"]
        },
        retrieval_metrics={
            "retrieval_latency": metrics["retrieval_latency"],
            "no_documents": metrics["retrieval_metrics_data"]["no_documents"],
            "best_score": metrics["retrieval_metrics_data"]["best_score"],
            "avg_score": metrics["retrieval_metrics_data"]["avg_score"],
            "confidence_score_pass": metrics["retrieval_metrics_data"]["best_score"] >= main.CONFIDENCE_THRESHOLD,
        },
        memory_usage={
            "cpu_percent": metrics["memory_usage"]["cpu_percent"],
            "ram_percent": metrics["memory_usage"]["ram_percent"],
            "ram_used_mb": metrics["memory_usage"]["ram_used_mb"]
        },
        blocked_input=blocked_input
    )
    return {
        "answer": answer,
        "blocked": blocked_input
    }