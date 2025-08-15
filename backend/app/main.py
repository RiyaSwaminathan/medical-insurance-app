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

def _to_bytes(x) -> bytes:
    if x is None:
        return b""
    if isinstance(x, bytes):
        return x
    return str(x).encode("utf-8")

def stream_generator(question: str):
    print("generate() called")
  
    try:
        for update in app_graph.stream({"question": question}, stream_mode="updates"):
        

            for _node, fields in update.items():
                if not isinstance(fields, dict):
                    continue

                for key in ("token", "answer", "output", "text", "content"):
                    if key in fields and fields[key]:
                        chunk = fields[key]
                        yield _to_bytes(chunk)
                msgs = fields.get("messages")
                if isinstance(msgs, list) and msgs:
                    last = msgs[-1]
                    if isinstance(last, dict) and "content" in last and last["content"]:
                        yield _to_bytes(last["content"])
    except Exception as e:
       
        err = f"\n[Backend error] {type(e).__name__}: {e}\n"
        yield _to_bytes(err)

@app.post("/query")
def query(req: QueryRequest):
    return StreamingResponse(stream_generator(req.question), media_type="text/plain")
