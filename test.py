import os
import asyncio
import logging
from app import aclient, DEFAULT_MODEL
from api_routes import analyze, improve, generate_setup
from models import AnalyzeRequest, ImproveRequest, GenerateSetupRequest
from repo_utils import clone_repo
from performance_utils import improve_repo_performance
from query_understanding import expand_code_query

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test repository URL
TEST_REPO_URL = "https://github.com/IsaacGemal/Bookmark-Sorter"

async def test_analyze():
    logger.info("Testing analyze functionality")
    request = AnalyzeRequest(repo_url=TEST_REPO_URL, query="Analyze the overall structure and potential performance bottlenecks")
    result = await analyze(request)
    logger.info(f"Analysis result: {result}")
    return result

async def test_improve():
    logger.info("Testing improve functionality")
    request = ImproveRequest(repo_url=TEST_REPO_URL)
    result = await improve(request)
    logger.info(f"Improvement suggestions: {result}")
    return result

async def test_generate_setup():
    logger.info("Testing generate setup script functionality")
    request = GenerateSetupRequest(repo_url=TEST_REPO_URL)
    result = await generate_setup(request)
    logger.info(f"Setup script: {result}")
    return result

async def create_bash_env_file(setup_script):
    logger.info("Creating bash environment file")
    with open("setup_env.sh", "w") as f:
        f.write("#!/bin/bash\n")
        f.write(setup_script['setup_script'])
    logger.info("Bash environment file created: setup_env.sh")

async def create_report(analysis_result, improvement_suggestions):
    logger.info("Creating comprehensive report")
    report = f"""
    Code Analysis Report
    ====================

    Repository: {TEST_REPO_URL}

    Comprehensive Analysis:
    {analysis_result['comprehensive_report']}

    Improvement Suggestions:
    {improvement_suggestions['improvements']}
    """
    with open("analysis_report.md", "w") as f:
        f.write(report)
    logger.info("Report created: analysis_report.md")

async def implement_improvements(repo_path, improvement_suggestions):
    logger.info("Implementing suggested improvements")
    # This is a simplified version. In a real scenario, you'd parse the suggestions
    # and apply them to the code automatically.
    for suggestion in improvement_suggestions['improvements']:
        logger.info(f"Implementing: {suggestion}")
        # Simulating implementation
        await asyncio.sleep(1)
    logger.info("Improvements implemented")

async def comprehensive_test():
    try:
        # Clone the repository
        repo_path = await clone_repo(TEST_REPO_URL, "./test_repo")

        # Analyze the repository
        analysis_result = await test_analyze()

        # Get improvement suggestions
        improvement_suggestions = await test_improve()

        # Generate setup script
        setup_script = await test_generate_setup()

        # Create bash environment file
        await create_bash_env_file(setup_script)

        # Create comprehensive report
        await create_report(analysis_result, improvement_suggestions)

        # Implement improvements
        await implement_improvements(repo_path, improvement_suggestions)

        logger.info("Comprehensive test completed successfully")
        logger.info(f"Analysis report saved as: {os.path.abspath('analysis_report.md')}")
        logger.info(f"Bash environment file saved as: {os.path.abspath('setup_env.sh')}")

    except Exception as e:
        logger.error(f"Error during comprehensive test: {str(e)}")

if __name__ == "__main__":
    asyncio.run(comprehensive_test())
