import os
import requests
from typing import TypedDict, List, Generator
from sqlalchemy import text
from dotenv import load_dotenv
from pathlib import Path
from langgraph.graph import StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from .db import SessionLocal
from .model import Chunk


env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent"

class GraphState(TypedDict):

    question: str
    context: str
    answer: str

def embed_query(query: str) -> List[float]:
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "models/embedding-001",
        "content": {"parts": [{"text": query}]},
        "task_type": "retrieval_query"
    }


    r = requests.post(f"{EMBED_URL}?key={GEMINI_API_KEY}", headers=headers, json=data)
    if r.status_code == 200:
        return r.json()["embedding"]["values"]
    return [0.0] * 768

def retrieve(state: GraphState) -> GraphState:

    query = state["question"]
    embedding = embed_query(query)
    vec_str = f"[{','.join(map(str, embedding))}]"
    db = SessionLocal()

    result = db.execute(
        text("""
            SELECT chunk FROM insurance_chunks
            ORDER BY embedding <-> :embedding
            LIMIT 3
        """),
        {"embedding": vec_str}
    )

    top_chunks = [row[0] for row in result.fetchall()]
    db.close()
    return {**state, "context": "\n\n".join(top_chunks)}

#debugging- printing backend logs to see if generation works
def generate(state: GraphState) -> Generator[GraphState, None, None]:
    print("generate() called", flush=True)
    print("Context:\n", state["context"], flush=True)
    print("Question:", state["question"], flush=True)

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.3
    )

    prompt = f"""
You are a helpful assistant. Use the following context to answer the question.

Context:
{state['context']}

Question: {state['question']}
"""
    answer = ""
    try:
        for chunk in llm.stream([HumanMessage(content=prompt)]):
            print("Gemini chunk:", chunk.content, flush=True)
            part = chunk.content or ""
            answer += part
            yield {**state, "answer": answer}
    except Exception as e:
        print("Gemini error:", str(e), flush=True)
        yield {**state, "answer": f"Gemini error: {str(e)}"}

def build_app_graph():
    graph = StateGraph(GraphState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate, is_generator=True)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.set_finish_point("generate")
    return graph.compile()

app_graph = build_app_graph()
