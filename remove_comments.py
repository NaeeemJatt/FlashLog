#!/usr/bin/env python3
"""
Script to remove all comments from Python files in the logai directory.
Handles both single-line (#) and multi-line (''' or \"\"\") comments.
"""

import os
import re
import ast
from pathlib import Path

def remove_comments_from_file(file_path):
    """Remove all comments from a Python file while preserving code structure."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Remove single-line comments (#)
        # This regex matches # comments but preserves # in strings
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                new_lines.append(line)
                continue
            
            # Find the first # that's not in a string
            in_string = False
            string_char = None
            comment_start = -1
            
            for i, char in enumerate(line):
                if char in ['"', "'"]:
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif string_char == char:
                        # Check if it's not escaped
                        if i == 0 or line[i-1] != '\\':
                            in_string = False
                            string_char = None
                elif char == '#' and not in_string:
                    comment_start = i
                    break
            
            if comment_start != -1:
                # Remove the comment part
                new_line = line[:comment_start].rstrip()
                if new_line:  # Keep the line if there's code before comment
                    new_lines.append(new_line)
                else:  # Skip empty lines that were just comments
                    new_lines.append('')
            else:
                new_lines.append(line)
        
        # Rejoin lines
        content = '\n'.join(new_lines)
        
        # Remove multi-line string comments (docstrings and multi-line comments)
        # This is more complex and requires AST parsing
        try:
            tree = ast.parse(content)
            
            # Remove docstrings from classes and functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    if (hasattr(node, 'body') and node.body and 
                        isinstance(node.body[0], ast.Expr) and 
                        isinstance(node.body[0].value, ast.Str)):
                        # Remove the first docstring
                        node.body = node.body[1:]
            
            # Convert back to source code
            try:
                import astor
                content = astor.to_source(tree)
            except ImportError:
                # If astor is not available, use a simpler approach
                # Remove triple-quoted strings that are not assignments
                content = re.sub(r'"""[^"]*"""', '', content, flags=re.DOTALL)
                content = re.sub(r"'''[^']*'''", '', content, flags=re.DOTALL)
        
        except SyntaxError:
            # If AST parsing fails, use regex approach
            # Remove triple-quoted strings that are not assignments
            content = re.sub(r'"""[^"]*"""', '', content, flags=re.DOTALL)
            content = re.sub(r"'''[^']*'''", '', content, flags=re.DOTALL)
        
        # Clean up extra blank lines
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            if line.strip() == '':
                if not prev_empty:
                    cleaned_lines.append(line)
                prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False
        
        content = '\n'.join(cleaned_lines)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Removed comments from: {file_path}")
            return True
        else:
            print(f"- No comments found in: {file_path}")
            return False
            
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def find_python_files(directory):
    """Find all Python files in the given directory and subdirectories."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', 'node_modules', '.idea']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    """Main function to remove comments from all Python files in logai directory."""
    logai_dir = 'logai'
    
    if not os.path.exists(logai_dir):
        print(f"Error: {logai_dir} directory not found!")
        return
    
    print(f"Searching for Python files in {logai_dir}...")
    python_files = find_python_files(logai_dir)
    
    print(f"Found {len(python_files)} Python files")
    print("=" * 50)
    
    processed_count = 0
    modified_count = 0
    
    for file_path in python_files:
        processed_count += 1
        if remove_comments_from_file(file_path):
            modified_count += 1
    
    print("=" * 50)
    print(f"Processing complete!")
    print(f"Total files processed: {processed_count}")
    print(f"Files modified: {modified_count}")

if __name__ == "__main__":
    main() 