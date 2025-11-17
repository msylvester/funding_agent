import streamlit as st
import sys
import os
from datetime import datetime

from services.huggingface_data import HuggingFaceDataService
from services.model_records_database import ModelRecordsDatabase
# from services.custom_agents.arg import simulation  # Commented out - not needed for current functionality
from langgraph.graph import END
from langchain_core.messages import AIMessage, HumanMessage

def huggingface_page():
    """Hugging Face Intelligence page"""
    
    st.title("🤗 Hugging Face Intelligence")
    
    if st.button("Get Trending Models", type="primary"):
        with st.spinner("Fetching trending models from Hugging Face..."):
            try:
                service = HuggingFaceDataService()
                db = ModelRecordsDatabase()

                models = service.get_trending_models(limit=20)

                if models:
                    # Separate models into new and existing
                    new_models = []
                    existing_models = []

                    for model in models:
                        # Check if model exists in database by full_name
                        existing_records = db.read_records_by_name(model['full_name'])

                        if not existing_records:
                            # New model - write to database
                            db.create_record(model['full_name'], datetime.utcnow())
                            new_models.append(model)
                        else:
                            # Existing model
                            existing_models.append(model)

                    st.success(f"Found {len(models)} trending models ({len(new_models)} new, {len(existing_models)} previously seen)")

                    # Display new models in highlighted table
                    if new_models:
                        st.markdown("### 🔥 Must See New")
                        new_models_html = """<style>
.new-table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
    overflow: hidden;
}
.new-table th {
    background-color: rgba(0, 0, 0, 0.3);
    color: white;
    padding: 15px;
    text-align: left;
    font-weight: bold;
}
.new-table td {
    padding: 12px 15px;
    color: white;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.new-table tr:hover {
    background-color: rgba(255, 255, 255, 0.1);
}
.new-table a {
    color: #ffd700;
    text-decoration: none;
    font-weight: bold;
}
.new-table a:hover {
    text-decoration: underline;
}
</style>
<table class="new-table">
    <thead>
        <tr>
            <th>Model</th>
            <th>Downloads</th>
            <th>Likes</th>
            <th>Link</th>
        </tr>
    </thead>
    <tbody>"""

                        for model in new_models:
                            downloads_text = f"{model['downloads']:,}" if model['downloads'] > 0 else "N/A"
                            likes_text = f"{model['likes']:,}" if model['likes'] > 0 else "N/A"

                            new_models_html += f"""
        <tr>
            <td><strong>{model['full_name']}</strong></td>
            <td>{downloads_text}</td>
            <td>{likes_text}</td>
            <td><a href="{model['url']}" target="_blank">View</a></td>
        </tr>"""

                        new_models_html += """
    </tbody>
</table>"""
                        st.markdown(new_models_html, unsafe_allow_html=True)

                    # Display existing models in regular table
                    if existing_models:
                        st.markdown("### 📚 Old School")
                        old_models_html = """<style>
.old-table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    background-color: #f8f9fa;
    border-radius: 10px;
    overflow: hidden;
}
.old-table th {
    background-color: #6c757d;
    color: white;
    padding: 15px;
    text-align: left;
    font-weight: bold;
}
.old-table td {
    padding: 12px 15px;
    color: #333;
    border-bottom: 1px solid #dee2e6;
}
.old-table tr:hover {
    background-color: #e9ecef;
}
.old-table a {
    color: #007bff;
    text-decoration: none;
}
.old-table a:hover {
    text-decoration: underline;
}
</style>
<table class="old-table">
    <thead>
        <tr>
            <th>Model</th>
            <th>Downloads</th>
            <th>Likes</th>
            <th>Link</th>
        </tr>
    </thead>
    <tbody>"""

                        for model in existing_models:
                            downloads_text = f"{model['downloads']:,}" if model['downloads'] > 0 else "N/A"
                            likes_text = f"{model['likes']:,}" if model['likes'] > 0 else "N/A"

                            old_models_html += f"""
        <tr>
            <td><strong>{model['full_name']}</strong></td>
            <td>{downloads_text}</td>
            <td>{likes_text}</td>
            <td><a href="{model['url']}" target="_blank">View</a></td>
        </tr>"""

                        old_models_html += """
    </tbody>
</table>"""
                        st.markdown(old_models_html, unsafe_allow_html=True)

                    # Close database connection
                    db.close_connection()
                else:
                    st.error("No trending models found")

            except Exception as e:
                st.error(f"Error fetching trending models: {str(e)}")
                st.info("Please check your internet connection and try again.")

    # Commented out due to agents.arg import conflict with openai-agents
    # if st.button("Start Sim", type="primary"):
    #     with st.spinner("Running simulation..."):
    #         try:
    #             st.subheader("Debate: Rust vs C++ for Video Game Development")

    #             # Run the simulation and collect messages
    #             for chunk in simulation.stream({"messages": []}, {"recursion_limit": 6}):
    #                 if END not in chunk:
    #                     # Extract messages from chunk
    #                     for node_name, node_data in chunk.items():
    #                         if 'messages' in node_data:
    #                             for message in node_data['messages']:
    #                                 # Determine which user is speaking
    #                                 if node_name == "chat_bot":
    #                                     speaker = "C++ Advocate"
    #                                     icon = "💙"
    #                                 else:  # simulated_user_node
    #                                     speaker = "Rust Advocate"
    #                                     icon = "🦀"

    #                                 # Display the argument
    #                                 with st.container():
    #                                     st.markdown(f"**{icon} {speaker}:**")
    #                                     st.write(message.content)
    #                                     st.divider()

    #             st.success("Simulation complete!")

    #         except Exception as e:
    #             st.error(f"Error running simulation: {str(e)}")
 
