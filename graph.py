import os
import json
from typing import TypedDict
import chromadb
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from langgraph.graph import StateGraph, START, END
from prompts import SUPPORT_PROMPT

# MOCK LLM configuration

MOCK_LLM = os.getenv("MOCK_LLM", "1")

# Pydantic output schema - Task 4

class SupportResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float = Field(ge=0.0, le=1.0)

# ChromaDB and embedding model

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path=CHROMA_DIR)

collection = client.get_collection(
    name="zepto_support"
)

# LangGraph state

class SupportState(TypedDict, total=False):
    query: str
    intent: str
    context: list[str]
    sources: list[str]
    answer: str
    confidence: float
    final_response: str

# Node 1: Classify intent

def classify_intent(state: SupportState):

    query = state["query"]
    query_lower = query.lower()

    policy_keywords = [
        "delivery",
        "return",
        "refund",
        "membership",
        "tracking",
        "cancel",
        "gift card",
        "support hours"
    ]

    if MOCK_LLM != "0":

        # Required graded mock mode
        if any(keyword in query_lower for keyword in policy_keywords):
            intent = "policy_question"
        else:
            intent = "general_question"

    else:

        # Optional real LLM mode
        intent = classify_with_real_llm(query)

    return {
        "intent": intent
    }

# Optional real LLM classification

def classify_with_real_llm(query: str):

    try:
        from langchain_groq import ChatGroq

        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0
        )

        prompt = f"""
Classify the following customer query as exactly one of:

policy_question
general_question

Return only the classification.

Query:
{query}
"""

        response = llm.invoke(prompt)

        result = response.content.strip().lower()

        if "policy_question" in result:
            return "policy_question"

        return "general_question"

    except Exception as exc:

        raise RuntimeError(
            "Real LLM mode requires a configured LLM backend."
        ) from exc


# Node 2: Retrieve and answer

def retrieve_and_answer(state: SupportState):

    query = state["query"]

    # Embed the query
    query_embedding = model.encode(query).tolist()

    # Retrieve top 3 chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    sources = [
        metadata["source"]
        for metadata in metadatas
    ]

    # Required mock mode

    if MOCK_LLM != "0":

        top_chunk_snippet = documents[0][:200]

        answer = (
            f"Based on the retrieved context: "
            f"{top_chunk_snippet}"
        )

        # Task 4: validate through Pydantic
        response = SupportResponse(
            answer=answer,
            sources=sources,
            confidence=1.0
        )

    # Optional real LLM mode

    else:

        context = "\n\n".join(documents)

        prompt = SUPPORT_PROMPT.format(
            context=context,
            question=query
        )

        response = answer_with_real_llm(
            prompt,
            sources
        )

    return {
        "context": documents,
        "sources": response.sources,
        "answer": response.answer,
        "confidence": response.confidence,
        "final_response": response.model_dump_json()
    }


# Optional real LLM answer generation

def answer_with_real_llm(
    prompt: str,
    sources: list[str]
):

    try:

        from langchain_groq import ChatGroq

        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0
        )

        corrective_instruction = """
Return ONLY valid JSON matching this exact schema:

{
    "answer": "string",
    "sources": ["string"],
    "confidence": 0.0
}

The confidence value must be between 0 and 1.
Do not include markdown or extra text.
"""

        for attempt in range(3):

            if attempt == 0:

                current_prompt = (
                    prompt
                    + "\n\n"
                    + corrective_instruction
                )

            else:

                current_prompt = (
                    prompt
                    + "\n\n"
                    + corrective_instruction
                    + "\n\n"
                    + "Your previous output was invalid. "
                    + "Correct it and return only valid JSON."
                )

            response = llm.invoke(current_prompt)

            try:

                raw_output = response.content.strip()

                data = json.loads(raw_output)

                validated = SupportResponse.model_validate(data)

                # Use the retrieved source IDs
                validated = SupportResponse(
                    answer=validated.answer,
                    sources=sources,
                    confidence=validated.confidence
                )

                return validated

            except Exception:

                if attempt == 2:

                    return SupportResponse(
                        answer=(
                            "ERROR: The LLM response could not "
                            "be validated against the required "
                            "JSON schema after 3 attempts."
                        ),
                        sources=[],
                        confidence=0.0
                    )

    except Exception as exc:

        raise RuntimeError(
            "Real LLM mode requires a configured LLM backend."
        ) from exc


# Node 3: Direct answer

def direct_answer(state: SupportState):

    if MOCK_LLM != "0":

        # Required graded mock mode
        response = SupportResponse(
            answer=(
                "I can only answer questions about "
                "Zepto policies right now."
            ),
            sources=[],
            confidence=1.0
        )

    else:

        # Optional real LLM mode
        prompt = SUPPORT_PROMPT.format(
            context="No policy context was retrieved.",
            question=state["query"]
        )

        response = answer_with_real_llm(
            prompt,
            []
        )

    return {
        "answer": response.answer,
        "sources": response.sources,
        "confidence": response.confidence,
        "final_response": response.model_dump_json()
    }


# Conditional routing

def route_intent(state: SupportState):

    if state["intent"] == "policy_question":
        return "retrieve_and_answer"

    return "direct_answer"


# Build LangGraph StateGraph

graph = StateGraph(SupportState)


graph.add_node(
    "classify_intent",
    classify_intent
)

graph.add_node(
    "retrieve_and_answer",
    retrieve_and_answer
)

graph.add_node(
    "direct_answer",
    direct_answer
)


graph.add_edge(
    START,
    "classify_intent"
)


graph.add_conditional_edges(
    "classify_intent",
    route_intent,
    {
        "retrieve_and_answer": "retrieve_and_answer",
        "direct_answer": "direct_answer"
    }
)


graph.add_edge(
    "retrieve_and_answer",
    END
)

graph.add_edge(
    "direct_answer",
    END
)


app = graph.compile()


# Test

if __name__ == "__main__":

    questions = [
        "How long does delivery take?",
        "What is the capital of India?"
    ]

    for question in questions:

        result = app.invoke({
            "query": question
        })

        print("\nQuestion:", question)
        print("Intent:", result["intent"])
        print("Final JSON:")
        print(result["final_response"])