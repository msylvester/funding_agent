#!/usr/bin/env python3
import os
import sys
import tempfile
import subprocess
import json
from pathlib import Path

class ExternalEditor:
    def __init__(self):
        self.config_dir = Path.home() / '.claude'
        self.config_dir.mkdir(exist_ok=True)

    def get_editor_command(self):
        """Get the preferred editor command"""
        # Check Claude Code config first
        editor = self.get_claude_config('editor')
        if editor:
            return editor

        # Fall back to environment variables
        editor = os.environ.get('CLAUDE_EDITOR') or os.environ.get('EDITOR') or os.environ.get('VISUAL')
        if editor:
            return editor

        # Default fallbacks in order of preference
        editors = ['code -w', 'vim', 'nano', 'emacs', 'gedit']

        for editor_cmd in editors:
            editor_name = editor_cmd.split()[0]
            if self.command_exists(editor_name):
                return editor_cmd

        return 'nano'  # Ultimate fallback

    def command_exists(self, command):
        """Check if a command exists in PATH"""
        try:
            subprocess.run(['which', command],
                         capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def get_claude_config(self, key):
        """Get configuration from Claude Code settings"""
        try:
            config_file = self.config_dir / 'settings.json'
            if config_file.exists():
                with open(config_file) as f:
                    config = json.load(f)
                return config.get('external_editor', {}).get(key)
        except:
            pass
        return None

    def create_template(self):
        """Create initial template for the editor"""
        template = """# Claude Code Prompt

Write your detailed instructions, questions, or requests below.
You can use markdown formatting.

## Instructions

<!-- Write your prompt here -->


## Context (Optional)

<!-- Add any relevant context, file references, or background -->


## Expected Output

<!-- Describe what kind of response you're looking for -->


---
<!-- Save and exit when done. Empty file cancels. -->
"""
        return template.strip()

    def open_editor(self):
        """Open external editor and return the content"""
        editor_cmd = self.get_editor_command()

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w+',
            suffix='.md',
            delete=False,
            prefix='claude_edit_'
        ) as tmp_file:
            # Write template
            tmp_file.write(self.create_template())
            tmp_file.flush()
            tmp_path = tmp_file.name

        try:
            print(f"Opening editor: {editor_cmd}")
            print(f"Editing: {tmp_path}")
            print("Save and exit when done, or exit without saving to cancel.")

            # Prepare editor command
            if editor_cmd.startswith('code'):
                # VS Code needs special handling for waiting
                cmd = editor_cmd.split() + [tmp_path]
            else:
                # For terminal editors, just pass the file
                cmd = editor_cmd.split() + [tmp_path]

            # Open the editor
            result = subprocess.run(cmd, check=False)

            # Check if user cancelled (non-zero exit in some editors is normal)
            if not os.path.exists(tmp_path):
                print("❌ Edit cancelled - file not found")
                return None

            # Read the content
            with open(tmp_path, 'r') as f:
                content = f.read().strip()

            # Clean up
            os.unlink(tmp_path)

            # Check if content is meaningful (not just the template)
            if not content or content == self.create_template().strip():
                print("❌ Edit cancelled - no content provided")
                return None

            # Remove template comments if they're still there
            content = self.clean_template_content(content)

            if not content.strip():
                print("❌ Edit cancelled - no meaningful content")
                return None

            return content

        except subprocess.CalledProcessError as e:
            print(f"❌ Editor failed: {e}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
        finally:
            # Ensure cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def clean_template_content(self, content):
        """Remove template comments and empty sections"""
        lines = content.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip template comments
            if line.strip().startswith('<!--') and line.strip().endswith('-->'):
                continue
            if line.strip() == '---':
                continue
            # Skip empty template sections
            if line.strip() in ['# Claude Code Prompt', '## Instructions', '## Context (Optional)', '## Expected Output']:
                # Only keep if followed by non-empty content
                continue
            cleaned_lines.append(line)

        # Remove excessive empty lines
        result = '\n'.join(cleaned_lines).strip()

        # Remove multiple consecutive newlines
        import re
        result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)

        return result

    def main(self):
        """Main entry point"""
        try:
            content = self.open_editor()

            if content:
                print("\n" + "="*50)
                print("📝 Content from editor:")
                print("="*50)
                print(content)
                print("="*50)
                print("\n✅ Ready to send to Claude!")

                # Save to history for reference
                self.save_to_history(content)

            else:
                print("❌ Edit cancelled or no content provided")

        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

    def save_to_history(self, content):
        """Save the prompt to history for reference"""
        try:
            history_file = self.config_dir / 'edit_history.jsonl'

            import time
            history_entry = {
                'timestamp': time.time(),
                'content': content,
                'editor': self.get_editor_command()
            }

            with open(history_file, 'a') as f:
                f.write(json.dumps(history_entry) + '\n')

        except Exception:
            # Don't fail if history save fails
            pass

if __name__ == '__main__':
    editor = ExternalEditor()
    editor.main()
