import streamlit as st
import sys
import os

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))

from hackernews_service import HackerNewsService

def hackernews_page():
    """Hacker News Intelligence page"""
    
    st.title("📰 Hacker News Intelligence")
    st.markdown("*AI-powered analysis of today's top tech stories*")
    
    if st.button("Get Top Stories", type="primary"):
        with st.spinner("Scraping Hacker News and analyzing stories with AI..."):
            try:
                # Load API configuration
                from config.settings import API_CONFIG
                
                # Initialize the service
                hn_service = HackerNewsService(
                    openrouter_api_key=API_CONFIG['openrouter_api_key'],
                    openrouter_base_url=API_CONFIG['openrouter_base_url'],
                    default_model=API_CONFIG['default_model']
                )
                
                # Get analyzed stories
                result = hn_service.get_top_analyzed_stories(story_limit=30)
                
                if result["success"]:
                    stories = result["stories"]
                    analysis_text = result.get("analysis", "")
                    total_scraped = result.get("total_scraped", 0)
                    
                    st.success(f"✨ Analyzed {total_scraped} stories and highlighted the top {len(stories)}")
                    
                    # Show the highlighted stories
                    if stories:
                        st.markdown("### 🔥 Top Stories Selected by AI")
                        
                        for i, story in enumerate(stories, 1):
                            # Create an expandable section for each story
                            with st.expander(f"#{story.get('rank', i)}: {story['title']} ({story['points']} points)"):
                                # Story metadata
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**👤 Author:** {story['author'] or 'Unknown'}")
                                    st.write(f"**⭐ Points:** {story['points']:,}")
                                    st.write(f"**💬 Comments:** {story['comments_count']:,}")
                                
                                with col2:
                                    st.write(f"**🌐 Domain:** {story['domain'] or 'N/A'}")
                                    st.write(f"**⏰ Posted:** {story['time_posted'] or 'Unknown'}")
                                    st.write(f"**📊 Rank:** #{story.get('rank', 'N/A')}")
                                
                                # AI Analysis (if available)
                                if story.get('analysis'):
                                    analysis = story['analysis']
                                    st.markdown("---")
                                    st.markdown("**🤖 AI Analysis:**")
                                    
                                    if analysis.get('significance'):
                                        st.write(f"**Why it matters:** {analysis['significance']}")
                                    
                                    if analysis.get('insights'):
                                        st.write(f"**Key insights:** {analysis['insights']}")
                                    
                                    if analysis.get('community_interest'):
                                        st.write(f"**Community interest:** {analysis['community_interest']}")
                                
                                # Links
                                st.markdown("---")
                                link_col1, link_col2 = st.columns(2)
                                with link_col1:
                                    if story['url'] and not story['url'].startswith('https://news.ycombinator.com'):
                                        st.markdown(f"🔗 [Read Article]({story['url']})")
                                    else:
                                        st.write("🔗 Discussion only")
                                
                                with link_col2:
                                    st.markdown(f"💬 [HN Discussion]({story['hn_url']})")
                        
                        # Show full analysis if available
                        if analysis_text and result.get("analysis_success"):
                            with st.expander("📊 View Full AI Analysis"):
                                st.markdown(analysis_text)
                    
                    else:
                        st.warning("No stories were highlighted by the AI analysis.")
                        
                else:
                    st.error(f"Failed to fetch stories: {result['message']}")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.info("Please check your API configuration and try again.")
    
    # Add some helpful information
    st.markdown("---")
    st.markdown("### About This Analysis")
    st.info("""
    This tool scrapes the latest stories from Hacker News and uses AI to identify the most significant ones based on:
    
    • **Tech relevance** and innovation potential
    • **Industry impact** and breaking news value  
    • **Community engagement** (points and comments)
    • **Emerging trends** in startup and development space
    
    The AI analyzes all stories and provides insights on why each highlighted story matters to the tech community.
    """)