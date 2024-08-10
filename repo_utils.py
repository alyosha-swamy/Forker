import os
import git
from models import Program, File
from typing import List
import logging
import shutil

logger = logging.getLogger(__name__)

async def clone_repo(repo_url: str, local_path: str) -> str:
    logger.info(f"Cloning repository from {repo_url} to {local_path}")
    if os.path.exists(local_path):
        logger.info(f"Directory {local_path} already exists. Removing it.")
        shutil.rmtree(local_path)
    git.Repo.clone_from(repo_url, local_path)
    logger.info("Repository cloned successfully")
    return local_path

async def create_knowledge_base(repo_path: str) -> List[str]:
    logger.info("Creating knowledge base from repository contents")
    knowledge_base = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if is_allowed_file(file):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        chunks = [content[i:i+1000] for i in range(0, len(content), 1000)]
                        knowledge_base.extend(chunks)
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {str(e)}")
    logger.info(f"Knowledge base created with {len(knowledge_base)} entries")
    return knowledge_base

def is_allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    allowed_extensions = ('.py', '.js', '.mdx', '.md', '.txt')
    return filename.lower().endswith(allowed_extensions)
