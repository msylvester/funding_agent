"""Web research agent workflow for company information."""

from __future__ import annotations
import os
import sys

# Add project root to path to enable services. imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from typing import Any

from agents import Agent, ModelSettings, Runner, RunConfig, TResponseInputItem, trace, WebSearchTool, AgentOutputSchema
from pydantic import BaseModel
from typing import Optional
from services.rag_service_agent import get_rag_tools


class RagResearchAgentSchema__CompaniesItem(BaseModel):
    company_name: str #REVISIT b/c its being gen'd
    description: str #i am worried that the decipriton is being generated {Comppan_name: company name Despriton: { Desciption }
    industry: Optional[str] = None
    relevance_score: Optional[float] = None


class RagResearchAgentSchema(BaseModel):
    companies: list[RagResearchAgentSchema__CompaniesItem]


class SummarizeAndDisplaySchema(BaseModel):
    company_name: str
    description: str
    industry: Optional[str] = None
    relevance_score: Optional[float] = None


class CompanyDetails(BaseModel):
    website: str
    company_size: str
    headquarters_location: str
    founded_year: float
    industry: str
    description: str


class WebResearchAgentSchema(BaseModel):
    companies: dict[str, CompanyDetails]  # key = company name


web_research_agent = Agent(
    name="Web research agent",
    instructions="""You are a research assistant that gathers additional company information using web search.

For each company provided, use web search to find:
- Official website URL
- Company size (number of employees, e.g., "10-50", "100-500", "1000+")
- Headquarters location (city, country)
- Year the company was founded
- Industry classification
- Brief description of what the company does

Output format: Return a dictionary where each key is the exact company name provided, and the value contains the company details.

Example output structure:
{
  "companies": {
    "Company Name Here": {
      "website": "https://...",
      "company_size": "10-50",
      "headquarters_location": "City, Country",
      "founded_year": 2020.0,
      "industry": "Technology",
      "description": "Brief description..."
    }
  }
}

Focus on finding accurate, up-to-date information from official sources. Search for each company individually to get the most accurate results.""",
    model="gpt-4o-mini",
    output_type=AgentOutputSchema(WebResearchAgentSchema, strict_json_schema=False),
    tools=[WebSearchTool()],
    model_settings=ModelSettings(
        store=True,
    ),
)




rag_research_agent = Agent(
    name="RAG research agent",
    instructions="""You are a research assistant with access to a RAG (Retrieval Augmented Generation) knowledge base
of funded startup companies.

Your available tools:
- rag_semantic_search: Search the vector database for relevant company documents
- rag_generate_reasoning: Synthesize information from retrieved documents
- rag_full_query: Combined search + reasoning in one call

Your workflow:
1. Use rag_semantic_search to find relevant company documents based on the query
2. Analyze the retrieved documents and their distance scores
3. Extract company information from the results to build your response

Guidelines:
- Lower distance scores indicate higher relevance (< 1.0 is very relevant, > 1.5 is loosely relevant)
- Focus on the company_name and description from the retrieved documents
- If no relevant documents are found, return an empty companies list
- Extract industry information from the document descriptions when possible
- Only include companies that were actually found in the RAG search results

Output your findings as a list of companies with the information retrieved from the database.""",
    model="gpt-4o",
    output_type=RagResearchAgentSchema,
    tools=get_rag_tools(),
    model_settings=ModelSettings(
        store=True,
    ),
)


summarize_and_display = Agent(
    name="Summarize and display",
    instructions="Put the research together in a nice display using the output format described.",
    model="gpt-4o",
    output_type=SummarizeAndDisplaySchema,
    model_settings=ModelSettings(
        store=True,
    ),
)


class WorkflowInput(BaseModel):
    input_as_text: str


async def run_research_workflow(input_text: str) -> dict[str, Any]:
    """
    Run the web research workflow.

    Args:
        input_text: The input query for research

    Returns:
        Dictionary containing the research results
    """
    workflow_input = WorkflowInput(input_as_text=input_text)
    workflow = workflow_input.model_dump()

    conversation_history: list[TResponseInputItem] = [
        {
            "role": "user",
            "content": [{"type": "input_text", "text": workflow["input_as_text"]}],
        }
    ]

    # Run RAG research agent
    rag_research_agent_result_temp = await Runner.run(
        rag_research_agent,
        input=conversation_history,
        run_config=RunConfig(
            trace_metadata={
                "__trace_source__": "agent-builder",
                "workflow_id": "wf_6909008d6bfc81909d1d9a9d8f3110c70af2d656afb56bf5",
            }
        ),
    )

    conversation_history.extend(
        [item.to_input_item() for item in rag_research_agent_result_temp.new_items]
    )

    rag_research_agent_result = {
        "output_text": rag_research_agent_result_temp.final_output.json(),
        "output_parsed": rag_research_agent_result_temp.final_output.model_dump(),
    }

    # Run web research agent for each company found by RAG
    companies_from_rag = rag_research_agent_result["output_parsed"]["companies"]

    if companies_from_rag:
        # Create prompt with just company names - agent instructions handle the rest
        company_names = [c["company_name"] for c in companies_from_rag]
        web_research_prompt = ', '.join(company_names)

        web_research_history: list[TResponseInputItem] = [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": web_research_prompt}],
            }
        ]

        web_research_agent_result_temp = await Runner.run(
            web_research_agent,
            input=web_research_history,
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "agent-builder",
                    "workflow_id": "wf_6909008d6bfc81909d1d9a9d8f3110c70af2d656afb56bf5",
                }
            ),
        )

        web_research_agent_result = {
            "output_text": web_research_agent_result_temp.final_output.json(),
            "output_parsed": web_research_agent_result_temp.final_output.model_dump(),
        }
    else:
        web_research_agent_result = {"output_parsed": {"companies": {}}}

    # Return RAG and web research results (no summary agent)
    return {
        "rag_research": rag_research_agent_result["output_parsed"],
        "web_research": web_research_agent_result["output_parsed"],
    }
