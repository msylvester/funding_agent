"""
Utilities for generating and displaying diffs
"""

import difflib
from typing import List, Tuple
import os


def generate_unified_diff(original_content: str, new_content: str, filename: str) -> str:
    """Generate a unified diff between original and new content."""
    original_lines = original_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
        lineterm=""
    )
    
    return ''.join(diff)


def format_diff_for_display(diff: str) -> str:
    """Format diff for better readability in Claude Code."""
    if not diff.strip():
        return "No changes detected."
    
    lines = diff.split('\n')
    formatted_lines = []
    
    for line in lines:
        if line.startswith('+++') or line.startswith('---'):
            formatted_lines.append(line)
        elif line.startswith('@@'):
            formatted_lines.append(line)
        elif line.startswith('+'):
            formatted_lines.append(f"+ {line[1:]}")
        elif line.startswith('-'):
            formatted_lines.append(f"- {line[1:]}")
        else:
            formatted_lines.append(f"  {line}")
    
    return '\n'.join(formatted_lines)


def extract_search_replace_blocks(content: str) -> List[Tuple[str, str]]:
    """Extract SEARCH/REPLACE blocks from content."""
    blocks = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        if '<<<<<<< SEARCH' in lines[i]:
            search_start = i + 1
            search_end = None
            replace_start = None
            replace_end = None
            
            # Find the divider and end
            for j in range(i + 1, len(lines)):
                if '=======' in lines[j]:
                    search_end = j
                    replace_start = j + 1
                elif '>>>>>>> REPLACE' in lines[j]:
                    replace_end = j
                    break
            
            if search_end is not None and replace_end is not None:
                search_content = '\n'.join(lines[search_start:search_end])
                replace_content = '\n'.join(lines[replace_start:replace_end])
                blocks.append((search_content, replace_content))
                i = replace_end + 1
            else:
                i += 1
        else:
            i += 1
    
    return blocks


def count_changes(diff: str) -> Tuple[int, int]:
    """Count additions and deletions in a diff."""
    additions = 0
    deletions = 0
    
    for line in diff.split('\n'):
        if line.startswith('+') and not line.startswith('+++'):
            additions += 1
        elif line.startswith('-') and not line.startswith('---'):
            deletions += 1
    
    return additions, deletions


def is_complex_edit(content: str, filename: str = "") -> bool:
    """Determine if an edit is complex enough to require confirmation."""
    # Check for SEARCH/REPLACE blocks
    search_replace_blocks = extract_search_replace_blocks(content)
    if len(search_replace_blocks) > 2:
        return True
    
    # Check file size
    lines = content.split('\n')
    if len(lines) > 50:
        return True
    
    # Check for certain file types that should always be confirmed
    sensitive_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs']
    if any(filename.endswith(ext) for ext in sensitive_extensions):
        return True
    
    return False
