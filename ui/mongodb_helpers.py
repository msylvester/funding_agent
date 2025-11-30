"""
Helper utilities for MongoDB data management in Streamlit
"""

import pandas as pd
from typing import List, Dict, Tuple, Set, Any
from services.database.database import FundingDatabase


def convert_records_to_dataframe(records: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, Dict[int, str]]:
    """
    Convert MongoDB records to pandas DataFrame for display and editing

    Args:
        records: List of MongoDB documents as dictionaries

    Returns:
        Tuple of (DataFrame, id_mapping)
        - DataFrame: Records formatted for st.data_editor
        - id_mapping: Dict mapping row index to ObjectId string
    """
    if not records:
        return pd.DataFrame(), {}

    # Create DataFrame from records
    df = pd.DataFrame(records)

    # Create index to ObjectId mapping
    id_mapping = {idx: record['_id'] for idx, record in enumerate(records)}

    # Reorder columns to put _id first
    cols = df.columns.tolist()
    if '_id' in cols:
        cols.remove('_id')
        cols = ['_id'] + cols
        df = df[cols]

    return df, id_mapping


def detect_changes(original_df: pd.DataFrame,
                  edited_df: pd.DataFrame,
                  id_mapping: Dict[int, str]) -> Tuple[Dict[str, Dict[str, Any]], Set[str]]:
    """
    Compare original and edited DataFrames to detect changes
    Uses _id column for reliable tracking instead of index positions

    Args:
        original_df: Original DataFrame before edits
        edited_df: DataFrame after user edits
        id_mapping: Mapping of row indices to ObjectIds (kept for compatibility but not used)

    Returns:
        Tuple of (edited_records, deleted_ids)
        - edited_records: Dict mapping ObjectId to changed fields {object_id: {field: new_value}}
        - deleted_ids: Set of ObjectIds that were deleted
    """
    edited_records = {}
    deleted_ids = set()

    # Define columns that should not trigger updates
    non_editable_cols = {'_id', 'created_at', 'updated_at'}

    # Get _id values from both DataFrames for deletion detection
    # This is more reliable than index-based tracking
    original_ids = set(original_df['_id'].values)
    edited_ids = set(edited_df['_id'].values)
    deleted_ids = original_ids - edited_ids

    # Detect edited rows by comparing rows with same _id
    for idx in edited_df.index:
        if idx not in original_df.index:
            continue  # Skip new rows if any

        # Use .loc[] for label-based indexing instead of .iloc[] for position-based
        original_row = original_df.loc[idx]
        edited_row = edited_df.loc[idx]

        # Ensure we're comparing the same record
        if original_row['_id'] != edited_row['_id']:
            continue

        # Track changed fields
        changes = {}
        for col in edited_df.columns:
            if col in non_editable_cols:
                continue

            # Handle NaN comparisons
            orig_val = original_row[col]
            edit_val = edited_row[col]

            # Safe NaN checking - handle both scalars and arrays
            try:
                both_nan = pd.isna(orig_val) and pd.isna(edit_val)
                if both_nan:
                    continue  # Both NaN, no change
            except (ValueError, TypeError):
                # Values are arrays/lists - pd.isna() returns array, can't use in if
                both_nan = False

            # Compare values
            try:
                if not both_nan and orig_val != edit_val:
                    changes[col] = edit_val
            except ValueError:
                # Direct comparison failed (likely arrays) - use pandas equals
                try:
                    if not pd.Series(orig_val).equals(pd.Series(edit_val)):
                        changes[col] = edit_val
                except:
                    # If all else fails, record the change
                    changes[col] = edit_val

        # If there are changes, store them using the _id from the row
        if changes:
            object_id = edited_row['_id']
            edited_records[object_id] = changes

    return edited_records, deleted_ids


def apply_updates_to_db(db: FundingDatabase, edited_records: Dict[str, Dict[str, Any]]) -> Tuple[int, List[str]]:
    """
    Apply update operations to MongoDB database

    Args:
        db: FundingDatabase instance
        edited_records: Dict mapping ObjectId to fields to update

    Returns:
        Tuple of (success_count, errors)
        - success_count: Number of successful updates
        - errors: List of error messages
    """
    success_count = 0
    errors = []

    for object_id, update_data in edited_records.items():
        try:
            success = db.update_company(object_id, update_data)
            if success:
                success_count += 1
            else:
                errors.append(f"Failed to update record {object_id[:8]}... (no rows modified)")
        except Exception as e:
            errors.append(f"Error updating record {object_id[:8]}...: {str(e)}")

    return success_count, errors


def apply_deletes_to_db(db: FundingDatabase, deleted_ids: Set[str]) -> Tuple[int, List[str]]:
    """
    Apply delete operations to MongoDB database

    Args:
        db: FundingDatabase instance
        deleted_ids: Set of ObjectIds to delete

    Returns:
        Tuple of (success_count, errors)
        - success_count: Number of successful deletions
        - errors: List of error messages
    """
    success_count = 0
    errors = []

    for object_id in deleted_ids:
        try:
            success = db.delete_company(object_id)
            if success:
                success_count += 1
            else:
                errors.append(f"Failed to delete record {object_id[:8]}... (not found)")
        except Exception as e:
            errors.append(f"Error deleting record {object_id[:8]}...: {str(e)}")

    return success_count, errors


def get_editable_columns(df: pd.DataFrame) -> List[str]:
    """
    Get list of columns that should be editable

    Args:
        df: DataFrame with all columns

    Returns:
        List of column names that should be editable
    """
    non_editable = {'_id', 'created_at', 'updated_at'}
    return [col for col in df.columns if col not in non_editable]
