"""
Research page for company information using AI agents
"""

import streamlit as st
import asyncio
import html
from services.orchestrator_workflow import run_orchestrator_workflow


def research_page():
    """Display the Research page with AI-powered company search and advice"""
    st.markdown("<h1>🔬 Research & Advice</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color: #666; margin-bottom: 2rem;'>Ask for advice about your product/startup, or research existing companies.</p>",
        unsafe_allow_html=True
    )

    # Search input and button
    col1, col2 = st.columns([4, 1])

    with col1:
        query = st.text_input(
            "Question or Company",
            placeholder="e.g., 'What investors would like my SaaS?' or 'Research Tesla'",
            label_visibility="collapsed",
            key="research_input"
        )

    with col2:
        search_button = st.button("🚀 Ask", use_container_width=True, type="primary")

    # Process search
    if search_button and query.strip():
        with st.spinner("🤖 AI agents analyzing your request..."):
            try:
                # Run the orchestrator workflow
                results = asyncio.run(run_orchestrator_workflow(query))

                # Store results in session state
                st.session_state['research_results'] = results
                st.session_state['last_research_query'] = query

            except Exception as e:
                st.error(f"❌ Error processing request: {str(e)}")
                st.session_state['research_results'] = None

    # Display results if available
    if 'research_results' in st.session_state and st.session_state['research_results']:
        results = st.session_state['research_results']
        query_text = st.session_state.get('last_research_query', 'Unknown')
        intent = results.get('intent', 'research')

        st.markdown("---")

        # Show intent classification (optional, for debugging)
        if results.get('reasoning'):
            with st.expander("🧠 Intent Classification", expanded=False):
                st.markdown(f"**Classified as:** {intent}")
                st.markdown(f"**Reasoning:** {results['reasoning']}")

        # Display based on intent
        if intent == "advice":
            st.markdown(f"### 💡 Advice for: *{query_text}*")

            advice_result = results.get('result', {})

            # --- Recommended Investors Cards ---
            investors_list = advice_result.get("advice", {}).get("investors", [])
            if investors_list:
                st.markdown("#### 📊 Recommended Investors")
                for investor_item in investors_list:
                    with st.container():
                        # Parse investor data
                        if isinstance(investor_item, dict):
                            investor_name = investor_item.get('investor', 'Unknown Investor')
                            company_name = investor_item.get('company', '')
                        else:
                            # Handle string format like "investor='IBM' company='Qedma'"
                            import re
                            investor_match = re.search(r"investor='([^']*)'", str(investor_item))
                            company_match = re.search(r"company='([^']*)'", str(investor_item))
                            investor_name = investor_match.group(1) if investor_match else str(investor_item)
                            company_name = company_match.group(1) if company_match else ''

                        # Escape HTML entities to prevent rendering issues
                        investor_escaped = html.escape(investor_name)
                        company_escaped = html.escape(company_name) if company_name else ""

                        st.markdown(
                            f"""
                            <div style='background-color: #f0f2f6; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; color: black;'>
                                <h1 style='margin-top: 0; color: black; font-size: 2rem;'>{investor_escaped}</h1>
                                {f"<p style='color: #666; margin-bottom: 0;'>{company_escaped}</p>" if company_name else ""}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )


            # --- Strategic Advice ---
            strategic_advice = advice_result.get('advice', {}).get('strategic_advice')
            if strategic_advice:
                st.markdown("#### 📋 Strategic Guidance")
                st.markdown(strategic_advice)


        else:
            # Display Research Results
            st.markdown(f"### 🔍 Research Results for: *{query_text}*")

            # Extract research results
            research_result = results.get('result', {})

            # Display Web Research Results (companies dict)
            web_research = research_result.get('web_research', {})
            companies_dict = web_research.get('companies', {})

            if companies_dict:
                st.markdown("#### 📊 Companies Found")

                for idx, (company_name, details) in enumerate(companies_dict.items(), 1):
                    # Create a card for each company
                    with st.container():
                        # Escape HTML entities to prevent rendering issues
                        company_name_escaped = html.escape(company_name)

                        st.markdown(
                            f"""
                            <div style='background-color: #f0f2f6; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;'>
                                <h3 style='margin-top: 0;'>{company_name_escaped}</h3>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Company details in columns
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown(f"**Industry:** {details.get('industry', 'N/A')}")
                            founded = details.get('founded_year', 'N/A')
                            # Handle float years (e.g., 2014.0 -> 2014)
                            if isinstance(founded, float):
                                founded = int(founded)
                            st.markdown(f"**Founded:** {founded}")
                            st.markdown(f"**Location:** {details.get('headquarters_location', 'N/A')}")

                        with col2:
                            st.markdown(f"**Size:** {details.get('company_size', 'N/A')}")
                            if details.get('website'):
                                st.markdown(f"**Website:** [{details['website']}]({details['website']})")

                        # Description
                        if details.get('description'):
                            st.markdown("**Description:**")
                            st.markdown(details['description'])

                        if idx < len(companies_dict):
                            st.markdown("---")
            else:
                st.info("No companies found matching your query.")

    # Show helpful message if no results yet
    elif search_button:
        st.info("👆 Enter your question and click Ask to get started")
    else:
        # Show example queries
        st.markdown("---")
        st.markdown("### 💡 Example Queries")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📋 Advice Examples:**")
            st.markdown("""
            - What investors would be interested in my SaaS product?
            - How should I pitch my AI startup?
            - Should I raise a seed round now?
            - What's the best go-to-market strategy for my marketplace?
            """)

        with col2:
            st.markdown("**🔍 Research Examples:**")
            st.markdown("""
            - Research Tesla
            - Tell me about SpaceX funding
            - What is Anthropic's business model?
            - Look up Stripe's investors
            """)
