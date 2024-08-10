from models import EnhancedCodeQuery, QueryPlan
from app import aclient
from datetime import date

async def expand_code_query(query: str, model: str) -> EnhancedCodeQuery:
    return await aclient.chat.completions.create(
        model=model,
        response_model=EnhancedCodeQuery,
        messages=[
            {
                "role": "system",
                "content": f"You're a query understanding system for code analysis. Today is {date.today()}. Expand and enhance the given query for better code analysis.",
            },
            {"role": "user", "content": f"query: {query}"},
        ],
    )

async def decompose_question(question: str, model: str) -> QueryPlan:
    return await aclient.chat.completions.create(
        model=model,
        response_model=QueryPlan,
        messages=[
            {
                "role": "system",
                "content": "You are a query understanding system capable of decomposing a question into subquestions for code analysis.",
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )
