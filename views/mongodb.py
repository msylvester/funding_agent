"""
MongoDB Records Management Page
Displays and allows editing of funding database records
"""

import os
import streamlit as st
import pandas as pd
from services.database.database import FundingDatabase
from services.database.dual_database_manager import DualDatabaseManager
from ui.mongodb_helpers import (
    convert_records_to_dataframe,
    detect_changes,
    apply_updates_to_db,
    apply_deletes_to_db,
    get_editable_columns
)


def mongodb_page():
    """Main MongoDB records management page"""

    # Page header
    st.title("📊 MongoDB Records Manager")
    st.markdown("View, edit, and manage all funding database records")

    # Initialize session state
    _initialize_session_state()

    # Top controls
    _render_top_controls()

    # Load data if not loaded or refresh requested
    if not st.session_state.mongodb_loaded:
        _load_mongodb_data()

    # Display table if we have data
    if st.session_state.mongodb_records:
        _display_editable_table()

        # Show pending changes summary and action buttons
        if st.session_state.pending_changes:
            st.markdown("---")
            _show_pending_changes_summary()
            _show_save_discard_buttons()
    else:
        st.info("No records found in database. The database might be empty or there might be a connection issue.")


def _initialize_session_state():
    """Initialize all session state variables for MongoDB management"""

    if 'mongodb_records' not in st.session_state:
        st.session_state.mongodb_records = []

    if 'mongodb_df' not in st.session_state:
        st.session_state.mongodb_df = None

    if 'mongodb_original_df' not in st.session_state:
        st.session_state.mongodb_original_df = None

    if 'mongodb_id_mapping' not in st.session_state:
        st.session_state.mongodb_id_mapping = {}

    if 'mongodb_loaded' not in st.session_state:
        st.session_state.mongodb_loaded = False

    if 'pending_changes' not in st.session_state:
        st.session_state.pending_changes = False

    if 'edited_rows' not in st.session_state:
        st.session_state.edited_rows = {}

    if 'deleted_ids' not in st.session_state:
        st.session_state.deleted_ids = set()


def _render_top_controls():
    """Render top control buttons"""

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("🔄 Refresh Data"):
            _refresh_data()
            st.rerun()

    with col3:
        if st.session_state.mongodb_records:
            st.metric("Total Records", len(st.session_state.mongodb_records))


def _load_mongodb_data():
    """Load data from MongoDB database"""

    with st.spinner("Loading database records..."):
        try:
            atlas_uri = os.getenv('MONGODB_ATLAS_URI')
            db = FundingDatabase(
                connection_string=atlas_uri,
                db_name='companies',
                collection_name='funded_companies'
            )
            records = db.read_all_companies(limit=1000)  # Load up to 1000 records
            db.close_connection()

            if records:
                st.session_state.mongodb_records = records
                df, id_mapping = convert_records_to_dataframe(records)
                st.session_state.mongodb_df = df
                st.session_state.mongodb_original_df = df.copy()
                st.session_state.mongodb_id_mapping = id_mapping
                st.session_state.mongodb_loaded = True
                st.session_state.pending_changes = False
                st.session_state.edited_rows = {}
                st.session_state.deleted_ids = set()
            else:
                st.session_state.mongodb_records = []
                st.session_state.mongodb_loaded = True

        except Exception as e:
            st.error(f"Error loading data from database: {str(e)}")
            st.session_state.mongodb_loaded = True


def _refresh_data():
    """Refresh data from database, discarding any pending changes"""
    st.session_state.mongodb_loaded = False
    st.session_state.pending_changes = False
    st.session_state.edited_rows = {}
    st.session_state.deleted_ids = set()


def _display_editable_table():
    """Display the editable data table"""

    st.markdown("### Edit Records")
    st.markdown("Click on any cell to edit. You can also delete rows by using the delete button in each row.")

    # Configure column display
    column_config = {
        "_id": st.column_config.TextColumn(
            "ID",
            width="small",
            disabled=True
        ),
        "company_name": st.column_config.TextColumn(
            "Company",
            width="medium"
        ),
        "funding_amount": st.column_config.TextColumn(
            "Funding",
            width="small"
        ),
        "series": st.column_config.TextColumn(
            "Series",
            width="small"
        ),
        "date": st.column_config.TextColumn(
            "Date",
            width="small"
        ),
        "investors": st.column_config.TextColumn(
            "Investors",
            width="medium"
        ),
        "source": st.column_config.TextColumn(
            "Source",
            width="small"
        ),
        "title": st.column_config.TextColumn(
            "Title",
            width="large"
        ),
        "description": st.column_config.TextColumn(
            "Description",
            width="large"
        ),
        "content": st.column_config.TextColumn(
            "Content",
            width="large"
        ),
        "created_at": st.column_config.TextColumn(
            "Created",
            width="small",
            disabled=True
        ),
        "updated_at": st.column_config.TextColumn(
            "Updated",
            width="small",
            disabled=True
        ),
    }

    # Display data editor
    edited_df = st.data_editor(
        st.session_state.mongodb_df,
        key="mongodb_editor",
        use_container_width=True,
        height=600,
        num_rows="dynamic",  # Allow row deletion
        column_config=column_config,
        hide_index=True
    )

    # Detect changes
    if edited_df is not None and st.session_state.mongodb_original_df is not None:
        edited_records, deleted_ids = detect_changes(
            st.session_state.mongodb_original_df,
            edited_df,
            st.session_state.mongodb_id_mapping
        )

        # Update session state
        st.session_state.edited_rows = edited_records
        st.session_state.deleted_ids = deleted_ids
        st.session_state.pending_changes = bool(edited_records or deleted_ids)

        # Update the current DataFrame
        st.session_state.mongodb_df = edited_df


def _show_pending_changes_summary():
    """Show summary of pending changes"""

    st.markdown("### 📝 Pending Changes")

    changes_text = []
    if st.session_state.edited_rows:
        changes_text.append(f"• {len(st.session_state.edited_rows)} row(s) edited")
    if st.session_state.deleted_ids:
        changes_text.append(f"• {len(st.session_state.deleted_ids)} row(s) marked for deletion")

    if changes_text:
        for text in changes_text:
            st.markdown(text)

        # Show detailed changes in expander
        with st.expander("View Details"):
            if st.session_state.edited_rows:
                st.markdown("**Edited Records:**")
                for object_id, changes in st.session_state.edited_rows.items():
                    st.write(f"- Record `{object_id[:12]}...`:")
                    for field, value in changes.items():
                        st.write(f"  - {field}: `{value}`")

            if st.session_state.deleted_ids:
                st.markdown("**Deleted Records:**")
                for object_id in st.session_state.deleted_ids:
                    st.write(f"- Record `{object_id[:12]}...`")


def _show_save_discard_buttons():
    """Show save and discard action buttons"""

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("✅ Save Changes", type="primary", use_container_width=True):
            _apply_changes_to_database()

    with col2:
        if st.button("❌ Discard Changes", use_container_width=True):
            _discard_changes()


def _find_local_id_by_url(url: str) -> str:
    """Find local database record ID by URL"""
    try:
        # Query local database
        local_uri = 'mongodb://localhost:27017/'
        local_db = FundingDatabase(
            connection_string=local_uri,
            db_name='funded_backup_20251105_121856',
            collection_name='companies'
        )
        # Find by URL
        local_records = local_db.collection.find({'url': url})
        for record in local_records:
            local_id = str(record['_id'])
            local_db.close_connection()
            return local_id
        local_db.close_connection()
    except Exception as e:
        raise Exception(f"Could not find local record for URL {url}: {e}")
    raise Exception(f"No local record found with URL {url}")


def _apply_changes_to_database():
    """Apply all pending changes to MongoDB database"""

    with st.spinner("Saving changes to database..."):
        try:
            update_count = 0
            delete_count = 0
            atlas_only_update_count = 0
            atlas_only_delete_count = 0
            update_errors = []
            delete_errors = []

            # Get Atlas database connection for Atlas-only operations
            atlas_uri = os.getenv('MONGODB_ATLAS_URI')
            atlas_db = FundingDatabase(
                connection_string=atlas_uri,
                db_name='companies',
                collection_name='funded_companies'
            )

            # Separate Atlas IDs into two groups: synced (in both DBs) and Atlas-only
            dual_edited_rows = {}
            atlas_only_edited_rows = {}

            if st.session_state.edited_rows:
                for atlas_id, changes in st.session_state.edited_rows.items():
                    record = next((r for r in st.session_state.mongodb_records if r['_id'] == atlas_id), None)
                    if record and record.get('url'):
                        try:
                            # Try to find local record
                            local_id = _find_local_id_by_url(record['url'])
                            dual_edited_rows[local_id] = changes
                        except:
                            # No local record - this is Atlas-only
                            atlas_only_edited_rows[atlas_id] = changes
                    else:
                        update_errors.append(f"Cannot update {atlas_id[:8]}...: No URL field")

            # Similar separation for deletions
            dual_deleted_ids = set()
            atlas_only_deleted_ids = set()

            if st.session_state.deleted_ids:
                for atlas_id in st.session_state.deleted_ids:
                    record = next((r for r in st.session_state.mongodb_records if r['_id'] == atlas_id), None)
                    if record and record.get('url'):
                        try:
                            local_id = _find_local_id_by_url(record['url'])
                            dual_deleted_ids.add(local_id)
                        except:
                            # No local record - this is Atlas-only
                            atlas_only_deleted_ids.add(atlas_id)
                    else:
                        delete_errors.append(f"Cannot delete {atlas_id[:8]}...: No URL field")

            # Handle dual-database operations (synced records)
            if dual_edited_rows or dual_deleted_ids:
                db = DualDatabaseManager()

                if dual_edited_rows:
                    count, errors = apply_updates_to_db(db, dual_edited_rows)
                    update_count += count
                    update_errors.extend(errors)

                if dual_deleted_ids:
                    count, errors = apply_deletes_to_db(db, dual_deleted_ids)
                    delete_count += count
                    delete_errors.extend(errors)

                db.close_connections()

            # Handle Atlas-only operations
            if atlas_only_edited_rows:
                for atlas_id, changes in atlas_only_edited_rows.items():
                    try:
                        if atlas_db.update_company(atlas_id, changes):
                            atlas_only_update_count += 1
                        else:
                            update_errors.append(f"Atlas-only update failed for {atlas_id[:8]}...")
                    except Exception as e:
                        update_errors.append(f"Atlas-only update error {atlas_id[:8]}...: {str(e)}")

            if atlas_only_deleted_ids:
                for atlas_id in atlas_only_deleted_ids:
                    try:
                        if atlas_db.delete_company(atlas_id):
                            atlas_only_delete_count += 1
                        else:
                            delete_errors.append(f"Atlas-only delete failed for {atlas_id[:8]}...")
                    except Exception as e:
                        delete_errors.append(f"Atlas-only delete error {atlas_id[:8]}...: {str(e)}")

            atlas_db.close_connection()

            # Show detailed results
            all_errors = update_errors + delete_errors

            if all_errors:
                st.error("Some operations failed:")
                for error in all_errors:
                    st.error(f"  - {error}")

            # Show success messages
            success_msgs = []
            if update_count > 0:
                success_msgs.append(f"{update_count} synced update(s)")
            if delete_count > 0:
                success_msgs.append(f"{delete_count} synced deletion(s)")
            if atlas_only_update_count > 0:
                success_msgs.append(f"{atlas_only_update_count} Atlas-only update(s)")
            if atlas_only_delete_count > 0:
                success_msgs.append(f"{atlas_only_delete_count} Atlas-only deletion(s)")

            if success_msgs:
                st.success(f"Successfully saved: {', '.join(success_msgs)}")
                if atlas_only_update_count > 0 or atlas_only_delete_count > 0:
                    st.info("Note: Some records only existed in Atlas and were not synced to local database")

                # Reload data to confirm changes
                _refresh_data()
                st.rerun()
            elif not all_errors:
                st.info("No changes to apply")

        except Exception as e:
            st.error(f"Error saving changes: {str(e)}")


def _discard_changes():
    """Discard all pending changes and reload original data"""

    # Reset to original DataFrame
    st.session_state.mongodb_df = st.session_state.mongodb_original_df.copy()
    st.session_state.pending_changes = False
    st.session_state.edited_rows = {}
    st.session_state.deleted_ids = set()

    st.success("Changes discarded")
    st.rerun()
