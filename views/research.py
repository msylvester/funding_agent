"""
Research page for company information using AI agents
"""

import streamlit as st
import asyncio
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
                for investor_name in investors_list:
                    with st.container():
                        st.markdown(
                            f"""
                            <div style='background-color: #f0f2f6; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; color: black;'>
                                <h3 style='margin-top: 0; color: black;'>{investor_name}</h3>
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

            # Extract research and summary from result
            research_result = results.get('result', {})

            # Display Summary
            if 'summary' in research_result and research_result['summary']:
                summary = research_result['summary']

                st.markdown("#### 📊 Summary")

                # Create a nice card for the summary
                with st.container():
                    st.markdown(
                        f"""
                        <div style='background-color: #f0f2f6; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;'>
                            <h3 style='margin-top: 0;'>{summary.get('company_name', 'N/A')}</h3>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # Company details in columns
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**Industry:** {summary.get('industry', 'N/A')}")
                        st.markdown(f"**Founded:** {summary.get('founded_year', 'N/A')}")
                        st.markdown(f"**Headquarters:** {summary.get('headquarters_location', 'N/A')}")

                    with col2:
                        st.markdown(f"**Company Size:** {summary.get('company_size', 'N/A')}")
                        if summary.get('website'):
                            st.markdown(f"**Website:** [{summary['website']}]({summary['website']})")

                    # Description
                    if summary.get('description'):
                        st.markdown("**Description:**")
                        st.markdown(summary['description'])

            # Display Detailed Research
            if 'research' in research_result and research_result['research']:
                research = research_result['research']

                if 'companies' in research and research['companies']:
                    st.markdown("---")
                    st.markdown("#### 📚 Detailed Research")

                    for idx, company in enumerate(research['companies'], 1):
                        with st.expander(f"{idx}. {company.get('company_name', 'Unknown Company')}", expanded=(idx == 1)):
                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown(f"**Industry:** {company.get('industry', 'N/A')}")
                                st.markdown(f"**Founded:** {company.get('founded_year', 'N/A')}")
                                st.markdown(f"**Headquarters:** {company.get('headquarters_location', 'N/A')}")

                            with col2:
                                st.markdown(f"**Company Size:** {company.get('company_size', 'N/A')}")
                                if company.get('website'):
                                    st.markdown(f"**Website:** [{company['website']}]({company['website']})")

                            # Description
                            if company.get('description'):
                                st.markdown("**Description:**")
                                st.markdown(company['description'])

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
