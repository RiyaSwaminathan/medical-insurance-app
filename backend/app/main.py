import sys
import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.langgraph_nodes import build_app_graph
from app.ingest import ingest_if_needed

sys.path.append(os.path.dirname(__file__))

app = FastAPI()

class QueryRequest(BaseModel):
    question: str

@app.on_event("startup")
def on_startup():
    ingest_if_needed()
    global app_graph
    app_graph = build_app_graph()


def stream_generator(question: str):
    for step in app_graph.stream({"question": question}):
        answer = step.get("answer")
        if answer:
            print("Streaming answer:", answer, flush=True)
            yield f"{answer}\n".encode("utf-8")


@app.post("/query")

def query(req: QueryRequest):
    return StreamingResponse(stream_generator(req.question), media_type="text/plain")

