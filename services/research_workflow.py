"""Web research agent workflow for company information."""

from __future__ import annotations

from typing import Any

from agents import Agent, ModelSettings, Runner, RunConfig, TResponseInputItem, trace
from pydantic import BaseModel


class WebResearchAgentSchema__CompaniesItem(BaseModel):
    company_name: str
    industry: str
    headquarters_location: str
    company_size: str
    website: str
    description: str
    founded_year: float


class WebResearchAgentSchema(BaseModel):
    companies: list[WebResearchAgentSchema__CompaniesItem]


class SummarizeAndDisplaySchema(BaseModel):
    company_name: str
    industry: str
    headquarters_location: str
    company_size: str
    website: str
    description: str
    founded_year: float


web_research_agent = Agent(
    name="Web research agent",
    instructions="You are a helpful assistant. Use web search to find information about the following company I can use in marketing asset based on the underlying topic.",
    model="gpt-4o-mini",
    output_type=WebResearchAgentSchema,
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
    with trace("New workflow"):
        workflow_input = WorkflowInput(input_as_text=input_text)
        workflow = workflow_input.model_dump()

        conversation_history: list[TResponseInputItem] = [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": workflow["input_as_text"]}],
            }
        ]

        # Run web research agent
        web_research_agent_result_temp = await Runner.run(
            web_research_agent,
            input=conversation_history,
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "agent-builder",
                    "workflow_id": "wf_6909008d6bfc81909d1d9a9d8f3110c70af2d656afb56bf5",
                }
            ),
        )

        conversation_history.extend(
            [item.to_input_item() for item in web_research_agent_result_temp.new_items]
        )

        web_research_agent_result = {
            "output_text": web_research_agent_result_temp.final_output.json(),
            "output_parsed": web_research_agent_result_temp.final_output.model_dump(),
        }

        # Run summarize and display agent
        summarize_and_display_result_temp = await Runner.run(
            summarize_and_display,
            input=conversation_history,
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "agent-builder",
                    "workflow_id": "wf_6909008d6bfc81909d1d9a9d8f3110c70af2d656afb56bf5",
                }
            ),
        )

        summarize_and_display_result = {
            "output_text": summarize_and_display_result_temp.final_output.json(),
            "output_parsed": summarize_and_display_result_temp.final_output.model_dump(),
        }

        # Return both research and summary results
        return {
            "research": web_research_agent_result["output_parsed"],
            "summary": summarize_and_display_result["output_parsed"],
        }
