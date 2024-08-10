from models import QueryPlan, Query, Search, KnowledgeGraph
from typing import List
import asyncio
from instructor import aclient

async def query_planner(question: str, model: str) -> QueryPlan:
    return await aclient.chat.completions.create(
        model=model,
        response_model=QueryPlan,
        messages=[
            {
                "role": "system",
                "content": "You are a world class query planning algorithm capable of breaking apart questions into its dependency queries such that the answers can be used to inform the parent question. Do not answer the questions, simply provide a correct compute graph with good specific questions to ask and relevant dependencies.",
            },
            {
                "role": "user",
                "content": f"Consider: {question}\nGenerate the correct query plan.",
            },
        ],
    )

async def segment_query(query: str, model: str) -> List[Search]:
    return await aclient.chat.completions.create(
        model=model,
        response_model=List[Search],
        messages=[
            {
                "role": "user",
                "content": f"Consider the query below: '\n{query}' and segment it into multiple search queries for a code repository. Use 'code' for code-related queries, 'documentation' for doc-related queries, and 'structure' for repo structure queries.",
            },
        ],
    )

async def execute_search(search: Search, knowledge_graph: KnowledgeGraph) -> str:
    return await search.execute(knowledge_graph)

async def execute_segmented_query(query: str, knowledge_graph: KnowledgeGraph) -> List[str]:
    searches = await segment_query(query)
    tasks = [execute_search(search, knowledge_graph) for search in searches]
    results = await asyncio.gather(*tasks)
    return results

async def execute_query(query: Query, knowledge_graph: KnowledgeGraph) -> str:
    return (await execute_segmented_query(query.question, knowledge_graph))[0]

async def execute_query_plan(plan: QueryPlan, knowledge_graph: KnowledgeGraph) -> dict:
    results = {}
    for query in plan.query_graph:
        if all(dep in results for dep in query.dependencies):
            context = "\n".join([results[dep] for dep in query.dependencies])
            result = await execute_query(query, knowledge_graph)
            results[query.id] = result
    return results
