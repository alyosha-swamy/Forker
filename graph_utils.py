from models import KnowledgeGraph, Node, Edge
from typing import List
import asyncio
from app import aclient

async def generate_graph(input: List[str], model: str) -> KnowledgeGraph:
    cur_state = KnowledgeGraph()  
    um_iterations = len(input)
    for i, inp in enumerate(input):
        new_updates = await aclient.chat.completions.create(
            model=model,
            response_model=KnowledgeGraph,
            messages=[
                {
                    "role": "system",
                    "content": "You are an iterative knowledge graph builder. You are given the current state of the graph, and you must append the nodes and edges to it. Do not provide any duplicates and try to reuse nodes as much as possible.",
                },
                {
                    "role": "user",
                    "content": f"Extract any new nodes and edges from the following:\n# Part {i}/{num_iterations} of the input:\n\n{inp}",
                },
                {
                    "role": "user",
                    "content": f"Here is the current state of the graph:\n{cur_state.model_dump_json(indent=2)}",
                },  
            ],
        )
        cur_state = cur_state.update(new_updates)  
    return cur_state
