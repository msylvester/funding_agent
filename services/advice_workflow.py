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

class AdviceSchema(BaseModel):
    investors: list[str]
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
1. Extract the sector/industry from their question (e.g., "SaaS", "AI", "fintech", "healthcare", "e-commerce")
2. Call search_funded_companies_by_sector(sector) to see what companies in that sector have been funded
3. Call get_investors_for_sector(sector) to get a ranked list of investors active in that sector
4. Analyze the data and prepare your response

Your output must be structured as follows:
- **investors**: Extract and return a list of investor/firm NAMES ONLY as strings (e.g., ["Sequoia Capital", "Andreessen Horowitz", "Y Combinator"]). Include the most relevant investors for the user's sector based on the data you retrieved.
- **strategic_advice**: Provide comprehensive, actionable strategic advice for the user. Include specific recommendations, insights about the sector, funding trends, which investors to prioritize and why, and reference relevant companies these investors have funded. This should be detailed guidance that helps the user approach these investors effectively.

**IMPORTANT - Handling Empty Results:**
If the tools return empty lists (no companies or investors found in the database):
- Set **investors** to an empty list: []
- In **strategic_advice**, explain that no matching investors were found in the database for this sector
- Suggest alternative keywords or broader categories the user could try (e.g., for "taco truck" suggest "food service", "restaurant", "food delivery")
- Provide general advice about finding investors for less common sectors
- DO NOT invent or hallucinate investor names. Only return investors that were actually found in the tool results.

Base your output entirely on the real data retrieved from the tools. Be specific and actionable.
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
You will receive startup funding advice and investor insights. Summarize key investor fit information concisely.

Output fields:
- investor_name: likely top-fit investor or firm mentioned
- industry: the key sector/opportunity discussed
- description: a narrative summary for a pitch deck or CRM note
""",
    model="gpt-4o",
    output_type=SummarizeAndDisplaySchema,
    model_settings=ModelSettings(store=True),
)


# ===============================
# WORKFLOW
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

        # Add advice messages to history for the summary agent
        conversation_history.extend(
            [item.to_input_item() for item in advice_result.new_items]
        )

        # Step 2: Run summarization agent
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
