"""
Unified Advice + Summary Display Workflow
"""

from __future__ import annotations
from typing import Any

from agents import Agent, ModelSettings, Runner, RunConfig, TResponseInputItem, trace
from pydantic import BaseModel

# Tools from your Mongo service
from mongodb_tools import (
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

1. Determine the sector/industry (e.g., "SaaS", "AI", "fintech", "healthcare", "e-commerce", "food delivery")
2. Call search_funded_companies_by_sector(sector) to retrieve funded companies in that category
   - This returns companies with their investors already linked
   - Each company has an "investors" field containing comma-separated investor names
3. Extract investor-company pairs from the search results:
   - For each company, split the "investors" field by comma
   - Create a pair for EACH investor: {investor: "Name", company: "Company Name"}
   - Example: If Calo has "AlJazira Capital, Nuwa Capital", create 2 pairs
4. Optionally call get_investors_for_sector(sector) for additional context about investor activity

### ✅ REQUIRED OUTPUT FORMAT

Return:

- **investors**: A list of objects with investor-company pairs:
  - `investor`: investor/firm name (from the company's investors field)
  - `company`: the company name that this investor funded

Example - if search returns Calo with investors "AlJazira Capital, Nuwa Capital":
[
  { "investor": "AlJazira Capital", "company": "Calo" },
  { "investor": "Nuwa Capital", "company": "Calo" }
]

- **strategic_advice**: Detailed, actionable guidance on approaching these investors and raising successfully in this sector.

### ❗ IMPORTANT RULES

- Extract ALL investors from the search results - don't filter them out
- Each investor from a company's "investors" field should become a separate pair
- Do NOT invent or add investors not present in the tool results
- If search returns no companies:
  - Return `investors: []`
  - Explain in `strategic_advice` that no matches were found in the database
  - Suggest broader search terms and general funding strategy

Be specific, structured, and actionable. Use ALL the data from tool results - don't leave investors out.
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
