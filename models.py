from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import List, Optional
from instructor import OpenAISchema
from datetime import date

class Node(BaseModel):
    id: int
    label: str
    color: str

class Edge(BaseModel):
    source: int
    target: int
    label: str
    color: str = "black"

class KnowledgeGraph(BaseModel):
    nodes: Optional[List[Node]] = Field(default_factory=list)
    edges: Optional[List[Edge]] = Field(default_factory=list)

    def update(self, other: "KnowledgeGraph") -> "KnowledgeGraph":
        return KnowledgeGraph(
            nodes=list(set(self.nodes + other.nodes)),
            edges=list(set(self.edges + other.edges)),
        )

class QueryType(Enum):
    SINGLE_QUESTION = "SINGLE"
    MERGE_MULTIPLE_RESPONSES = "MERGE_MULTIPLE_RESPONSES"

class Query(BaseModel):
    id: int = Field(..., description="Unique id of the query")
    question: str = Field(..., description="Question asked using a question answering system")
    dependencies: List[int] = Field(default_factory=list, description="List of sub questions that need to be answered before asking this question")
    node_type: QueryType = Field(default=QueryType.SINGLE_QUESTION, description="Type of question, either a single question or a multi-question merge")

class QueryPlan(BaseModel):
    query_graph: List[Query] = Field(..., description="The query graph representing the plan")

class Search(BaseModel):
    query: str = Field(..., description="Query to search for relevant content")
    type: str = Field(..., description="Type of search")

class File(OpenAISchema):
    file_name: str = Field(..., description="The name of the file including the extension")
    body: str = Field(..., description="Correct contents of a file")

class Program(OpenAISchema):
    files: List[File] = Field(..., description="List of files")

class Diff(OpenAISchema):
    diff: str = Field(
        ...,
        description=(
            "Changes in a code repository correctly represented in 'diff' format, "
            "correctly escaped so it could be used in a JSON"
        ),
    )

class Suggestion(BaseModel):
    title: str
    description: str
    estimated_impact: str
    score: float = Field(..., ge=0, le=1, description="Score indicating the priority of the suggestion")

class ImplementationInstructions(BaseModel):
    suggestion: Suggestion
    steps: List[str]
    code_changes: Optional[str]

class Extraction(BaseModel):
    topic: str
    summary: str
    hypothetical_questions: List[str] = Field(
        default_factory=list,
        description="Hypothetical questions that this code snippet could answer",
    )
    keywords: List[str] = Field(
        default_factory=list, description="Keywords that this code snippet is about"
    )

class DateRange(BaseModel):
    start: date
    end: date

class EnhancedCodeQuery(BaseModel):
    rewritten_query: str = Field(
        description="Rewrite the query to make it more specific to code analysis"
    )
    relevant_timeframe: Optional[DateRange] = Field(
        default=None,
        description="Relevant timeframe for the code analysis, if applicable"
    )
    analysis_focus: List[str] = Field(
        description="Specific aspects of code to focus on (e.g., 'performance', 'security', 'style')"
    )

class AnalyzeRequest(BaseModel):
    repo_url: str = Field(..., description="URL of the GitHub repository")
    model: str = Field(default="claude-3-5-sonnet-20240620", description="Model to use for analysis")
    query: str = Field(..., description="User's original query for code analysis")

    @validator('repo_url', 'query')
    def check_not_empty(cls, v):
        if not v.strip():
            raise ValueError("This field cannot be empty")
        return v

class ImproveRequest(BaseModel):
    repo_url: str = Field(..., description="URL of the GitHub repository")
    model: str = Field(default="claude-3-5-sonnet-20240620", description="Model to use for improvement suggestions")

    @validator('repo_url')
    def check_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Repository URL cannot be empty")
        return v

class GenerateSetupRequest(BaseModel):
    repo_url: str = Field(..., description="URL of the GitHub repository")
    model: str = Field(default="claude-3-5-sonnet-20240620", description="Model to use for setup script generation")

    @validator('repo_url')
    def check_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Repository URL cannot be empty")
        return v

class Question(BaseModel):
    id: int = Field(..., description="A unique identifier for the question")
    query: str = Field(..., description="The question decomposed as much as possible")
    subquestions: List[int] = Field(
        default_factory=list,
        description="The subquestions that this question is composed of",
    )

class QueryPlan(BaseModel):
    root_question: str = Field(..., description="The root question that the user asked")
    plan: List[Question] = Field(
        ..., description="The plan to answer the root question and its subquestions"
    )
