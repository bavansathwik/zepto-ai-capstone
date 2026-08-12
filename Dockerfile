FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    pydantic \
    chromadb \
    sentence-transformers \
    langgraph

ENV MOCK_LLM=1

EXPOSE 7860

CMD ["uvicorn", "api:api", "--host", "0.0.0.0", "--port", "7860"]