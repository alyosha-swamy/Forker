from fastapi import APIRouter, HTTPException
from models import AnalyzeRequest, ImproveRequest, GenerateSetupRequest, Program, File
from repo_utils import clone_repo
from analysis_utils import rag_analyze_repo
from performance_utils import improve_repo_performance
from query_understanding import expand_code_query
from app import aclient
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    try:
        repo_path = await clone_repo(request.repo_url, "./temp_repo")
        enhanced_query = await expand_code_query(request.query, request.model)
        analysis = await rag_analyze_repo(repo_path, enhanced_query, request.model)
        if not analysis or 'comprehensive_report' not in analysis:
            logger.warning("rag_analyze_repo returned unexpected result")
            analysis = {"comprehensive_report": "Analysis failed to produce a comprehensive report."}
        return {"analysis": analysis, "enhanced_query": enhanced_query.model_dump()}
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {str(e)}")


@router.post("/improve")
async def improve(request: ImproveRequest):
    try:
        repo_path = await clone_repo(request.repo_url, "./temp_repo")
        improvements = await improve_repo_performance(repo_path, request.model)
        return {"improvements": improvements}
    except Exception as e:
        logger.error(f"Error during improvement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-setup-script")
async def generate_setup(request: GenerateSetupRequest):
    try:
        repo_path = await clone_repo(request.repo_url, "./temp_repo")
        program = Program(files=[File(file_name=f, body=open(os.path.join(repo_path, f), 'r').read()) for f in os.listdir(repo_path) if os.path.isfile(os.path.join(repo_path, f))])
        script = await generate_setup_script(program, request.model)
        return {"setup_script": script}
    except Exception as e:
        logger.error(f"Error during setup script generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_setup_script(program: Program, model: str) -> str:
    response = await aclient.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an expert DevOps engineer. Generate a bash setup script for the given program files.",
            },
            {
                "role": "user",
                "content": f"Program files:\n{program.model_dump_json(indent=2)}\n\nGenerate a bash setup script:",
            },
        ],
    )
    return response.choices[0].message.content
