import streamlit as st
import streamlit.components.v1 as components
from ui.styles import apply_custom_styles
from services.open_source_langgraph import run_github_workflow

def opensource_page():
    """Open Source Intelligence page"""

    st.title("🔓 Open Source Intelligence")
    st.markdown("Discover trending repositories, ecosystem insights, and AI-curated must-see projects")

    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        language = st.selectbox(
            "Programming Language",
            options=[None, "Python", "JavaScript", "TypeScript", "Go", "Rust", "Java"],
            format_func=lambda x: "All Languages" if x is None else x
        )
    with col2:
        time_range = st.selectbox(
            "Time Range",
            options=["daily", "weekly", "monthly"],
            index=0
        )
    with col3:
        st.write("")  # Spacer
        st.write("")  # Spacer

                     
    if st.button("🚀 Analyze GitHub Ecosystem", type="primary", use_container_width=True):
        with st.spinner("Running LangGraph workflow: fetching trending repos, awesome lists, analyzing trends..."):
            result = run_github_workflow(
                language=language.lower() if language else None,
                time_range=time_range
            )

            if not result:
                st.error("Workflow failed to execute")
                return

            # Section 1: Must-See Repositories (AI-Selected)
            st.markdown("---")
            st.markdown("## 🌟 Must-See Repositories")
            st.markdown("*AI-curated selection of the most innovative and impactful projects*")

            must_see_repos = result.get('must_see_repos', [])
            if must_see_repos:
                for i, repo in enumerate(must_see_repos, 1):
                    with st.expander(f"⭐ #{i} - {repo['name']} ({repo['stars']:,} stars)", expanded=(i <= 3)):
                        col_a, col_b = st.columns([3, 1])
                        with col_a:
                            components.html(
                                """
                                <button onclick="alert('hey')" style="
                                    padding: 8px 16px;
                                    background-color: #FF4B4B;
                                    color: white;
                                    border: none;
                                    border-radius: 4px;
                                    cursor: pointer;
                                    font-size: 14px;
                                    font-weight: 500;
                                ">👍 Like</button>
                                """,
                                height=50
                            )
                            st.write(f"**Description:** {(repo.get('description') or 'No description')[:200]}")
                            if 'ai_reasoning' in repo:
                                st.info(f"💡 **Why it's must-see:** {repo['ai_reasoning']}")
                        with col_b:
                            st.metric("Stars", f"{repo['stars']:,}")
                            if repo.get('language'):
                                st.write(f"**Language:** {repo['language']}")

                        if repo.get('url'):
                            st.markdown(f"[🔗 View on GitHub]({repo['url']})")
            else:
                st.warning("No must-see repositories selected")

            # Section 2: Ecosystem Analysis
            '''
            st.markdown("---")
            st.markdown("## 📊 Ecosystem Analysis")

            analysis = result.get('analysis', {})
            if analysis:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Repos Analyzed", analysis.get('total_repos_analyzed', 0))
                with col2:
                    st.metric("Avg Stars", f"{analysis.get('average_stars', 0):,}")
                with col3:
                    st.metric("Total Stars", f"{analysis.get('total_stars', 0):,}")

                col_lang, col_topics = st.columns(2)

                with col_lang:
                    st.markdown("### 💻 Trending Languages")
                    trending_langs = analysis.get('trending_languages', [])
                    if trending_langs:
                        for lang_data in trending_langs[:5]:
                            st.write(f"- **{lang_data['language']}**: {lang_data['count']} repos")
                    else:
                        st.write("No language data")

                with col_topics:
                    st.markdown("### 🔥 Hot Topics")
                    hot_topics = analysis.get('hot_topics', [])
                    if hot_topics:
                        topics_str = ", ".join([f"`{t['topic']}`" for t in hot_topics[:8]])
                        st.markdown(topics_str)
                    else:
                        st.write("No topic data")
'''
            # Section 3: All Trending Repositories
            st.markdown("---")
            st.markdown("## 📈 All Trending Repositories")

            trending_repos = result.get('enriched_repos', result.get('trending_repos', []))
            if trending_repos:
                st.success(f"Found {len(trending_repos)} trending repositories")

                for repo in trending_repos:
                    stars_gained_text = f" (+{repo.get('stars_gained', 0)} today)" if repo.get('stars_gained') else ""

                    with st.expander(f"📦 {repo['name']} ({repo.get('stars', 0):,} stars{stars_gained_text})"):
                        st.write(f"**Owner:** {repo.get('owner', 'N/A')}")
                        st.write(f"**Description:** {repo.get('description') or 'No description'}")
                        st.write(f"**Language:** {repo.get('language') or 'Not specified'}")
                        st.write(f"**Forks:** {repo.get('forks', 'N/A')}")
                        if repo.get('url'):
                            st.write(f"**URL:** {repo['url']}")
                        if repo.get('topics'):
                            st.write(f"**Topics:** {', '.join(repo['topics'][:10])}")
            else:
                st.warning("No trending repositories found")

            # Section 4: Awesome Lists
            st.markdown("---")
            st.markdown("## ⭐ Awesome Lists")
            st.markdown("*Curated collections of awesome resources*")

            awesome_lists = result.get('awesome_lists', [])
            if awesome_lists:
                st.info(f"Discovered {len(awesome_lists)} awesome lists")

                cols = st.columns(2)
                for i, awesome in enumerate(awesome_lists[:10]):  # Show top 10
                    with cols[i % 2]:
                        with st.container():
                            st.write(f"**{awesome['name']}**")
                            st.caption(f"{awesome.get('stars', 0):,} stars • {awesome.get('description', 'No description')[:80]}")
                            if awesome.get('url'):
                                st.markdown(f"[View List]({awesome['url']})")
                            st.markdown("---")
            else:
                st.info("No awesome lists found")
