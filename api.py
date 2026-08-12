from fastapi import FastAPI
from pydantic import BaseModel
from graph import app as support_graph
from graph import SupportResponse

# Create FastAPI application
api = FastAPI(
    title="Zepto Support Assistant",
    description="Zepto policy support API",
    version="1.0"
)

# Request model

class AskRequest(BaseModel):
    query: str

# POST /ask

@api.post("/ask", response_model=SupportResponse)
def ask(request: AskRequest):

    result = support_graph.invoke({
        "query": request.query
    })

    return SupportResponse(
        answer=result["answer"],
        sources=result["sources"],
        confidence=result["confidence"]
    )