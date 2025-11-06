"""
Unified Advice + Summary Display Workflow
"""

from __future__ import annotations
from typing import Any

from agents import Agent, ModelSettings, Runner, RunConfig, TResponseInputItem, trace
from pydantic import BaseModel

# Tools from your Mongo service
from services.mongodb_tools import (
    search_funded_companies_by_sector,
    get_investors_for_sector,
)

# ===============================
# SCHEMAS
# ===============================

class InvestorCompanyPair(BaseModel):
    investor: str
    company: str

class AdviceSchema(BaseModel):
    investors: list[InvestorCompanyPair]
    strategic_advice: str

class SummarizeAndDisplaySchema(BaseModel):
    investor_name: str
    industry: str
    description: str

# ===============================
# ADVICE AGENT
# ===============================

advice_agent = Agent(
    name="Startup advice agent",
    instructions="""
You are a data-driven startup and product advisor with access to a database of funded companies and investors.

When users ask about investors for their product:

1. Determine the sector/industry (e.g., "SaaS", "AI", "fintech", "healthcare", "e-commerce")
2. Call search_funded_companies_by_sector(sector) to retrieve funded companies in that category
3. Call get_investors_for_sector(sector) to retrieve investors active in that category
4. Match investors to companies where possible (based on the data the tools return)

### ✅ REQUIRED OUTPUT FORMAT

Return:

- **investors**: A list of objects, each containing:
  - `investor`: investor/firm name
  - `company`: a company they funded in that sector (best match you can find)

Example:
[
  { "investor": "Sequoia Capital", "company": "Stripe" },
  { "investor": "Andreessen Horowitz", "company": "Coinbase" }
]

- **strategic_advice**: Detailed, actionable guidance on approaching these investors and raising successfully in this sector.

### ❗ IMPORTANT RULES

- Only return investors found from the tool data
- If you cannot match an investor to a specific company, do NOT invent one - leave it out
- If results are empty:
  - Return `investors: []`
  - Explain in `strategic_advice` that no matches were found in the database
  - Suggest broader keywords and a general funding strategy

Be specific, structured, and actionable. Do not hallucinate. Base everything on tool results.
""",
    model="gpt-4o",
    output_type=AdviceSchema,
    tools=[search_funded_companies_by_sector, get_investors_for_sector],
    model_settings=ModelSettings(store=True),
)

# ===============================
# SUMMARIZE & DISPLAY AGENT
# ===============================

summarize_and_display = Agent(
    name="Summarize and display",
    instructions="""
You will receive structured investor + company matches and strategic advice.

Summarize the most likely top-fit investor and opportunity clearly for a dashboard/CRM.

Output fields:
- investor_name: the best matching investor
- industry: primary sector discussed
- description: brief narrative summary
""",
    model="gpt-4o",
    output_type=SummarizeAndDisplaySchema,
    model_settings=ModelSettings(store=True),
)

# ===============================
# STANDALONE ADVICE FUNCTION (for testing)
# ===============================

async def get_investor_advice(input_text: str) -> dict[str, Any]:
    """
    Run just the advice agent to get investor recommendations.

    This is a standalone function for testing purposes, mirroring the pattern
    of classify_intent() in research_classifier.py. It runs ONLY the advice agent
    without the summarization step.

    Args:
        input_text: The user's query about their product/startup

    Returns:
        Dictionary with:
            - investors: List of {investor, company} pairs
            - strategic_advice: Detailed strategic guidance text
    """
    with trace("Investor advice (standalone)"):
        conversation_history: list[TResponseInputItem] = [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": input_text}],
            }
        ]

        advice_result = await Runner.run(
            advice_agent,
            input=conversation_history,
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "advice-agent-standalone",
                    "workflow_id": "advice_standalone",
                }
            ),
        )

        return {
            "investors": [
                {"investor": pair.investor, "company": pair.company}
                for pair in advice_result.final_output.investors
            ],
            "strategic_advice": advice_result.final_output.strategic_advice,
        }

# ===============================
# FULL WORKFLOW (for production)
# ===============================

async def run_advice_workflow(input_text: str) -> dict[str, Any]:
    """
    Run the entire workflow: investor advice → summary display output.
    """
    with trace("Advice workflow v2"):
        conversation_history: list[TResponseInputItem] = [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": input_text}],
            }
        ]

        # Step 1: Run the advice agent
        advice_result = await Runner.run(
            advice_agent,
            input=conversation_history,
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "advice-workflow",
                    "workflow_id": "advice_v2_with_summary",
                }
            ),
        )

        advice_output = {
            "investors": advice_result.final_output.investors,
            "strategic_advice": advice_result.final_output.strategic_advice,
        }

        # Add advice messages to history
        conversation_history.extend(
            [item.to_input_item() for item in advice_result.new_items]
        )

        # Step 2: Summarize
        summarize_and_display_result = await Runner.run(
            summarize_and_display,
            input=conversation_history,
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "summary-step",
                    "workflow_id": "advice_v2_with_summary",
                }
            ),
        )

        summary_output = summarize_and_display_result.final_output.model_dump()

        return {
            "advice": advice_output,
            "summary_display": summary_output,
        }
