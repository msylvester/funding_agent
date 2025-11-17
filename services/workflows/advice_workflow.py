"""
Unified Advice + Summary Display Workflow
"""

from __future__ import annotations
import os
import sys

# Add project root to path to enable services. imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(parent_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from typing import Any
import asyncio

from agents import Agent, ModelSettings, Runner, RunConfig, TResponseInputItem, trace
from pydantic import BaseModel

# Tools from your Mongo service
from mongodb_tools import (
    search_funded_companies_by_sector,
    get_investors_for_sector,
)

# Sector classification agent
try:
    from services.sector_agent import classify_sector
except ImportError:
    from sector_agent import classify_sector

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

1. Use the sector classification provided in the system message to search for relevant companies
   - The sector has already been determined by a classification agent and will be provided in a system message
   - Use this exact sector value when calling the search tools
   - The sector will look like: "SaaS", "AI", "fintech", "healthcare", "e-commerce", "food delivery", "quantum computing", etc.
2. Call search_funded_companies_by_sector(sector) using the exact sector from the system message
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
  - In `strategic_advice`, reference the ACTUAL SECTOR from the system message (e.g., "quantum computing", "Social Media", etc.)
  - Explain that no specific investor data was found for that particular sector in the database
  - Suggest broader search terms and general funding strategy for that sector

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
        # Step 1: Classify the sector using the sector agent
        sector_classification = classify_sector(input_text)

        # Step 2: Prepare conversation with sector context
        conversation_history: list[TResponseInputItem] = [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": f"The user's startup has been classified into the following sector: {sector_classification.sector}"}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": input_text}],
            }
        ]

        # Step 3: Run advice agent with classified sector
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


def get_investor_advice_sync(input_text: str) -> dict[str, Any]:
    """
    Synchronous wrapper for get_investor_advice() for use in testing harness.

    This allows the eval harness to call the advice agent synchronously,
    matching the pattern used in sector_harness.py.

    Args:
        input_text: The user's query about their product/startup

    Returns:
        Dictionary with:
            - investors: List of {investor, company} pairs
            - strategic_advice: Detailed strategic guidance text
    """
    return asyncio.run(get_investor_advice(input_text))


# ===============================
# FULL WORKFLOW (for production)
# ===============================

async def run_advice_workflow(input_text: str) -> dict[str, Any]:
    """
    Run the entire workflow: sector classification → investor advice → summary display output.
    """
    with trace("Advice workflow v2"):
        # Step 1: Classify the sector using the sector agent
        sector_classification = classify_sector(input_text)

        # Log the classification
        print(f"\n[Sector Classification]")
        print(f"  Sector: {sector_classification.sector}")
        print(f"  Confidence: {sector_classification.confidence:.2f}")
        print(f"  Rationale: {sector_classification.rationale}\n")

        # Step 2: Prepare conversation with sector context
        conversation_history: list[TResponseInputItem] = [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": f"The user's startup has been classified into the following sector: {sector_classification.sector}"}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": input_text}],
            }
        ]

        # Check if confidence is too low to provide specific recommendations
        if sector_classification.confidence < 0.8:
            print(f"[WARNING] Confidence ({sector_classification.confidence:.2f}) is below threshold (0.9). Returning generic response.\n")
            return {
                "advice": {
                    "investors": [],
                    "strategic_advice": (
                        f"I wasn't able to confidently classify your startup into a specific sector "
                        f"(confidence: {sector_classification.confidence:.2f}). "
                        f"To provide accurate investor recommendations, I need a clearer understanding of your industry.\n\n"
                        f"**General Fundraising Advice:**\n\n"
                        f"1. **Clarify Your Value Proposition**: Clearly articulate what problem you solve and for whom. "
                        f"This helps investors understand your market positioning.\n\n"
                        f"2. **Research Sector-Specific Investors**: Once you've refined your sector focus, "
                        f"look for investors who have a track record in your specific industry.\n\n"
                        f"3. **Build Traction First**: Demonstrating product-market fit, customer adoption, "
                        f"or revenue can make you more attractive to investors across any sector.\n\n"
                        f"4. **Network Within Your Industry**: Attend sector-specific events and conferences "
                        f"to meet investors who understand your space.\n\n"
                        f"Try rephrasing your query with more specific details about your product, "
                        f"target market, or industry to get tailored investor recommendations."
                    )
                },
                "summary_display": {
                    "investor_name": "N/A - Low Confidence Classification",
                    "industry": sector_classification.sector,
                    "description": (
                        f"Unable to provide specific investor recommendations due to low sector "
                        f"classification confidence ({sector_classification.confidence:.2f}). "
                        f"Generic fundraising advice provided instead."
                    )
                }
            }

        # Step 3: Run the advice agent
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

        # Step 4: Summarize
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
