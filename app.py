import os
import logging
import instructor
from litellm import Router
import wandb
from fastapi import FastAPI

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_MODEL = "claude-3-5-sonnet-20240620"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
USE_WANDB = os.getenv("USE_WANDB", "true").lower() == "true"

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")

# Initialize the Router and Instructor client
router = Router(
    model_list=[
        {
            "model_name": DEFAULT_MODEL,
            "capx_params": {
                "model": DEFAULT_MODEL,
                "api_key": ANTHROPIC_API_KEY,
            },
        }
    ],
    default_litellm_params={"acompletion": True},
)

aclient = instructor.patch(router)

# Create FastAPI app
app = FastAPI()

def init_wandb():
    if USE_WANDB:
        wandb.init(project="code-analysis-rag", config={"model": DEFAULT_MODEL})
        logger.info("Weights and Biases initialized")
    else:
        logger.info("Weights and Biases initialization skipped")

# Initialize Weights and Biases
init_wandb()

# You can add any additional setup or utility functions here if needed

# Make the client and app available for import in other modules
__all__ = ['aclient', 'DEFAULT_MODEL', 'app']
