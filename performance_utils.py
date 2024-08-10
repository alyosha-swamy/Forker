import ast
import os
import asyncio
import radon.complexity as radon_cc
import pylint.lint
from pylint.reporters.text import TextReporter
from io import StringIO
from typing import List, Dict
import git
from models import Suggestion, ImplementationInstructions, KnowledgeGraph, EnhancedCodeQuery
from app import aclient
from analysis_utils import analyze_files, rag_analyze_repo

async def generate_performance_suggestions(knowledge_graph: KnowledgeGraph, report: str, model: str) -> List[Suggestion]:
    completion = await aclient.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an expert code analyst. Based on the provided knowledge graph and analysis report, generate the top 4 suggestions to improve the performance of the code. Assign a score between 0 and 1 to each suggestion, with 1 being the highest priority.",
            },
            {
                "role": "user",
                "content": f"Knowledge Graph:\n{knowledge_graph.model_dump_json(indent=2)}\n\nAnalysis Report:\n{report}\n\nGenerate the top 4 performance improvement suggestions with scores.",
            },
        ],
        response_model=List[Suggestion],
        max_tokens=1000,
    )
    return completion

async def generate_implementation_instructions(suggestion: Suggestion, knowledge_graph: KnowledgeGraph, model: str) -> ImplementationInstructions:
    completion = await aclient.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an expert software engineer. Provide detailed instructions on how to implement the given performance improvement suggestion.",
            },
            {
                "role": "user",
                "content": f"Suggestion:\n{suggestion.model_dump_json(indent=2)}\n\nKnowledge Graph:\n{knowledge_graph.model_dump_json(indent=2)}\n\nProvide step-by-step instructions and any necessary code changes to implement this suggestion.",
            },
        ],
        response_model=ImplementationInstructions,
        max_tokens=1500,
    )
    return completion

async def analyze_code_aspect(file_path: str, aspect: str) -> Dict[str, float]:
    if aspect == "complexity":
        return {"complexity": analyze_code_complexity(file_path)}
    elif aspect == "style":
        return {"style_score": analyze_code_style(file_path)}
    elif aspect == "performance":
        return {"performance_score": analyze_code_performance(file_path)}
    else:
        return {}

def analyze_code_complexity(file_path: str) -> float:
    with open(file_path, 'r') as file:
        code = file.read()
    try:
        complexity = radon_cc.cc_visit(code)
        if complexity:
            return sum(item.complexity for item in complexity) / len(complexity)
        return 0
    except:
        return 0

def analyze_code_style(file_path: str) -> float:
    pylint_output = StringIO()
    reporter = TextReporter(pylint_output)
    pylint.lint.Run([file_path], reporter=reporter, do_exit=False)
    return 10 - float(pylint_output.getvalue().split('\n')[-3].split('/')[0])

def analyze_code_performance(file_path: str) -> float:
    with open(file_path, 'r') as file:
        code = file.read()
    tree = ast.parse(code)
    
    class PerformanceVisitor(ast.NodeVisitor):
        def __init__(self):
            self.loops = 0
            self.function_calls = 0
            self.list_comprehensions = 0

        def visit_For(self, node):
            self.loops += 1
            self.generic_visit(node)

        def visit_While(self, node):
            self.loops += 1
            self.generic_visit(node)

        def visit_Call(self, node):
            self.function_calls += 1
            self.generic_visit(node)

        def visit_ListComp(self, node):
            self.list_comprehensions += 1
            self.generic_visit(node)

    visitor = PerformanceVisitor()
    visitor.visit(tree)
    
    # Calculate a simple performance score
    score = 10 - (visitor.loops * 0.5 + visitor.function_calls * 0.3 + visitor.list_comprehensions * 0.2)
    return max(0, min(score, 10)) / 10  # Normalize to 0-1 range

async def analyze_performance_bottlenecks(repo_path: str) -> Dict[str, Dict[str, float]]:
    bottlenecks = {}
    aspects = ["complexity", "style", "performance"]
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                tasks = [analyze_code_aspect(file_path, aspect) for aspect in aspects]
                results = await asyncio.gather(*tasks)
                bottlenecks[file_path] = {k: v for d in results for k, v in d.items()}
    
    return bottlenecks

async def improve_repo_performance(repo_path: str, model: str) -> str:
    knowledge_graph = await analyze_files(repo_path, model)
    enhanced_query = EnhancedCodeQuery(
        rewritten_query="Provide a comprehensive analysis of the code structure and potential performance bottlenecks.",
        relevant_timeframe=None,
        analysis_focus=["performance", "complexity", "style"]
    )
    report = await rag_analyze_repo(repo_path, enhanced_query, model)
    
    bottlenecks = await analyze_performance_bottlenecks(repo_path)
    report += f"\n\nPerformance Bottlenecks:\n{bottlenecks}"
    
    suggestions = await generate_performance_suggestions(knowledge_graph, report, model)
    
    # Sort suggestions by score in descending order
    suggestions.sort(key=lambda x: x.score, reverse=True)
    
    implemented_suggestions = []
    for suggestion in suggestions[:2]:  # Implement top 2 suggestions
        instructions = await generate_implementation_instructions(suggestion, knowledge_graph, model)
        result = await implement_suggestion(repo_path, instructions)
        implemented_suggestions.append(result)
    
    return "\n".join(implemented_suggestions)

async def implement_suggestion(repo_path: str, instructions: ImplementationInstructions) -> str:
    repo = git.Repo(repo_path)
    branch_name = f"implement-{instructions.suggestion.title.lower().replace(' ', '-')}"
    repo.git.checkout('-b', branch_name)

    try:
        if instructions.code_changes:
            file_path = os.path.join(repo_path, instructions.suggestion.title.lower().replace(' ', '_') + '_changes.py')
            with open(file_path, 'w') as f:
                f.write(instructions.code_changes)
            repo.git.add(file_path)
        
        commit_message = f"Implement performance improvement: {instructions.suggestion.title}"
        repo.git.commit('-m', commit_message)
        
        return f"Changes implemented for suggestion: {instructions.suggestion.title} in branch {branch_name}"
    except Exception as e:
        repo.git.checkout('master')
        repo.git.branch('-D', branch_name)
        return f"Failed to implement suggestion: {instructions.suggestion.title}. Error: {str(e)}"
