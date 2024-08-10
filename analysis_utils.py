from models import KnowledgeGraph, Extraction, EnhancedCodeQuery
from typing import List, Dict, Optional
from datetime import date
from app import aclient
from repo_utils import create_knowledge_base
from graph_utils import generate_graph
import asyncio
import logging

logger = logging.getLogger(__name__)

async def extract_info(text_chunk: str, model: str) -> Optional[Extraction]:
    try:
        return await aclient.chat.completions.create(
            model=model,
            response_model=Extraction,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert code analyst. Extract key information from the given code snippet.",
                },
                {"role": "user", "content": text_chunk},
            ],
        )
    except Exception as e:
        logger.error(f"Error in extract_info: {str(e)}")
        return None

async def generate_follow_up_questions(analysis: str, model: str) -> List[str]:
    try:
        response = await aclient.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert code analyst. Based on the given analysis, generate 3 follow-up questions to explore the codebase further.",
                },
                {"role": "user", "content": f"Analysis:\n{analysis}\n\nGenerate 3 follow-up questions:"},
            ],
        )
        if response and response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.split('\n')
        else:
            logger.warning("Unexpected response structure in generate_follow_up_questions")
            return []
    except Exception as e:
        logger.error(f"Error in generate_follow_up_questions: {str(e)}")
        return []

async def rag_analyze_repo(repo_path: str, enhanced_query: EnhancedCodeQuery, model: str, max_iterations: int = 3) -> Dict[str, str]:
    knowledge_base = await create_knowledge_base(repo_path)
    comprehensive_report = ""
    follow_up_questions = []
    
    for iteration in range(max_iterations):
        if iteration == 0:
            query = enhanced_query.rewritten_query
        elif follow_up_questions:
            query = follow_up_questions[0]  # Use the first follow-up question
        else:
            break  # No more questions to ask
        
        try:
            # Use asyncio.gather to properly handle async operations
            extraction_tasks = [extract_info(chunk, model) for chunk in knowledge_base]
            extractions = await asyncio.gather(*extraction_tasks, return_exceptions=True)
            
            # Filter out any failed extractions and log errors
            valid_extractions = []
            for i, ext in enumerate(extractions):
                if isinstance(ext, Exception):
                    logger.error(f"Error in extraction {i}: {str(ext)}")
                else:
                    valid_extractions.append(ext)
            
            relevant_extractions = [
                ext for ext in valid_extractions
                if ext and any(kw.lower() in query.lower() for kw in ext.keywords)
            ]
            
            if not relevant_extractions:
                logger.warning(f"No relevant extractions found for query: {query}")
                comprehensive_report += f"\n\nIteration {iteration + 1}:\nQuestion: {query}\nAnalysis: No relevant information found.\n"
                break
            
            context = "\n".join([f"Topic: {ext.topic}\nSummary: {ext.summary}" for ext in relevant_extractions])
            
            response = await aclient.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an expert code analyst. Use the provided context to answer the question about the repository. Focus on the following aspects: {', '.join(enhanced_query.analysis_focus)}",
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}",
                    },
                ],
            )
            
            analysis = response.choices[0].message.content
            comprehensive_report += f"\n\nIteration {iteration + 1}:\nQuestion: {query}\nAnalysis: {analysis}\n"
            
            if iteration < max_iterations - 1:
                follow_up_questions = await generate_follow_up_questions(analysis, model)
        except Exception as e:
            logger.error(f"Error in rag_analyze_repo iteration {iteration}: {str(e)}")
            comprehensive_report += f"\n\nIteration {iteration + 1}:\nQuestion: {query}\nAnalysis: Error occurred during analysis.\n"
            break
    
    return {"comprehensive_report": comprehensive_report}

async def analyze_files(repo_path: str, model: str) -> KnowledgeGraph:
    knowledge_base = await create_knowledge_base(repo_path)
    return await generate_graph(knowledge_base, model=model)
