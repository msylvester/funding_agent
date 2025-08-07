import streamlit as st
from ui.styles import apply_custom_styles
from services.open_source_data_service import AggregatedOpenSourceService

def opensource_page():
    """Open Source Intelligence page"""
    
    # Apply custom CSS styling
    
    st.title("Open Source Intelligence")
    
    if st.button("Get Projects", type="primary"):
        with st.spinner("Fetching trending repositories from multiple sources..."):
            service = AggregatedOpenSourceService()
            repos = service.get_aggregated_trending(language=None)
            
            if repos:
                st.success(f"Found {len(repos)} repositories")
                
                for repo in repos:
                    # Source indicator
                    source_emoji = {
                        'trending': '🔥',
                        'api': '🔍', 
                        'both': '⭐'
                    }.get(repo.get('source', 'unknown'), '❓')
                    
                    # Stars gained display
                    stars_gained_text = f" (+{repo['stars_gained']} today)" if repo.get('stars_gained') else ""
                    
                    with st.expander(f"{source_emoji} {repo['name']} ({repo['stars']:,} stars{stars_gained_text})"):
                        st.write(f"**Owner:** {repo['owner']}")
                        st.write(f"**Description:** {repo['description'] or 'No description'}")
                        st.write(f"**Language:** {repo['language'] or 'Not specified'}")
                        st.write(f"**Forks:** {repo.get('forks', 'N/A')}")
                        st.write(f"**Source:** {'GitHub Trending' if repo['source'] == 'trending' else 'GitHub API' if repo['source'] == 'api' else 'Both Sources'}")
                        st.write(f"**URL:** {repo['url']}")
                        if repo.get('topics'):
                            st.write(f"**Topics:** {', '.join(repo['topics'])}")
            else:
                st.error("No repositories found")
