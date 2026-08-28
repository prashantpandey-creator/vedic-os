import sys

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "r") as f:
    content = f.read()

old_apply = """def apply_search_replace(file_path, search_block, replace_block, workspace_dir="."):
    file_path = os.path.join(workspace_dir, file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Standardize newlines and handle literal backslashes
    search_block = search_block.replace("\\r\\n", "\\n")
    replace_block = replace_block.replace("\\r\\n", "\\n")
    
    # Simple strict exact replace for now (1 instance max to avoid destroying duplicate blocks)
    new_content = content.replace(search_block, replace_block, 1)
    
    if new_content == content:
        raise Exception("Search block not found exactly in the file.")
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)"""

new_apply = """def apply_search_replace(file_path, search_block, replace_block, workspace_dir="."):
    import difflib
    
    file_path = os.path.join(workspace_dir, file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    search_block = search_block.replace("\\r\\n", "\\n")
    replace_block = replace_block.replace("\\r\\n", "\\n")
    
    new_content = content.replace(search_block, replace_block, 1)
    
    if new_content == content:
        raise Exception("Search block not found exactly in the file.")
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    # Generate visual diff
    diff = list(difflib.unified_diff(
        content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=file_path,
        tofile=file_path
    ))
    return "".join(diff)"""
content = content.replace(old_apply, new_apply)

with open("/Users/badenath/projects/local-llm-ui/core/file_system.py", "w") as f:
    f.write(content)

print("Git Diff patched in file_system.py")
