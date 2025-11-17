"""
Orchestrator workflow that classifies user intent and routes to appropriate agent workflow
Handles both advice requests and research requests
"""

from __future__ import annotations
from typing import Any

from agents import Agent, ModelSettings, Runner, RunConfig, TResponseInputItem, trace
from pydantic import BaseModel

from services.workflows.advice_workflow import run_advice_workflow
from services.workflows.research_workflow import run_research_workflow


# ===============================
# INTENT CLASSIFICATION SCHEMA
# ===============================

class IntentClassificationSchema(BaseModel):
    """Schema for intent classification result"""
    intent: str  # "advice" or "research"
    reasoning: str  # Explanation of classification


# ===============================
# INTENT CLASSIFIER AGENT
# ===============================

intent_classifier_agent = Agent(
    name="Intent classifier",
    instructions="""
You are an intent classifier that determines whether a user query is asking for:

1. **ADVICE** - Questions about fundraising, investors, startup strategy, product advice, or recommendations
   Examples:
   - "What investors would be interested in my SaaS product?"
   - "How should I pitch my AI startup?"
   - "Should I raise a seed round now?"
   - "What's the best go-to-market strategy for my marketplace?"
   - "Who should I talk to about raising for my fintech?"

2. **RESEARCH** - Questions about specific companies, their details, funding history, or general information
   Examples:
   - "Research Tesla"
   - "Tell me about SpaceX funding"
   - "What is Anthropic's business model?"
   - "Look up Stripe's investors"
   - "Find information about OpenAI"

Analyze the user's query and determine the intent.

Return:
- **intent**: Either "advice" or "research"
- **reasoning**: Brief explanation (1-2 sentences) of why you classified it this way

### CLASSIFICATION RULES

- If the query asks about what investors to approach, how to raise, or seeks strategic recommendations → **advice**
- If the query asks about a specific company's information, details, or history → **research**
- If unclear, default to **research**
- Look for keywords like "my product", "my startup", "should I", "how to" → **advice**
- Look for keywords like "research", "tell me about", "look up", company names → **research**
""",
    model="gpt-4o-mini",
    output_type=IntentClassificationSchema,
    model_settings=ModelSettings(store=True),
)


# ===============================
# INTENT CLASSIFICATION FUNCTION
# ===============================

async def classify_intent(query: str) -> dict[str, Any]:
    """
    Classify user query intent using AI agent

    Args:
        query: User's input query

    Returns:
        Dictionary with:
            - intent: "advice" or "research"
            - reasoning: Explanation of classification
    """
    with trace("Intent classification"):
        conversation_history: list[TResponseInputItem] = [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": query}],
            }
        ]

        classification_result = await Runner.run(
            intent_classifier_agent,
            input=conversation_history,
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "intent-classifier",
                    "workflow_id": "orchestrator_intent_classification",
                }
            ),
        )

        return {
            "intent": classification_result.final_output.intent,
            "reasoning": classification_result.final_output.reasoning,
        }


# ===============================
# ORCHESTRATOR WORKFLOW
# ===============================

async def run_orchestrator_workflow(query: str) -> dict[str, Any]:
    """
    Main orchestrator workflow that classifies intent and routes to appropriate workflow

    Args:
        query: User's input query

    Returns:
        Dictionary with:
            - intent: "advice" or "research"
            - reasoning: Classification reasoning
            - result: Results from the executed workflow
    """
    with trace("Orchestrator workflow"):
        # Step 1: Classify intent
        classification = await classify_intent(query)

        intent = classification["intent"]
        reasoning = classification["reasoning"]

        # Step 2: Route to appropriate workflow based on intent
        if intent == "advice":
            # Run advice workflow
            workflow_result = await run_advice_workflow(query)

            return {
                "intent": intent,
                "reasoning": reasoning,
                "result": workflow_result,
            }

        else:  # intent == "research" or default
            # Run research workflow
            workflow_result = await run_research_workflow(query)

            return {
                "intent": "research",
                "reasoning": reasoning,
                "result": workflow_result,
            }


# ===============================
# TESTING
# ===============================

if __name__ == "__main__":
    import asyncio

    async def test_orchestrator():
        """Test the orchestrator with different queries"""

        test_queries = [
            "What investors would be interested in my SaaS product?",
            "Research Tesla",
            "Tell me about SpaceX funding",
            "How should I pitch my AI startup?",
        ]

        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"{'='*60}")

            result = await run_orchestrator_workflow(query)

            print(f"\nIntent: {result['intent']}")
            print(f"Reasoning: {result['reasoning']}")
            print(f"\nResult keys: {list(result['result'].keys())}")

    # Run test
    asyncio.run(test_orchestrator())
