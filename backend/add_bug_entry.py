"""
Script để thêm bug entry vào Bug_Fixes_Documentation.md với UTF-8 encoding
"""
import re

# Read the original file
with open('doc/Bug_Fixes_Documentation.md', 'r', encoding='utf-8') as f:
    content = f.read()

# New table of contents entry
new_toc_entry = "1.  [04/12/2025 - Report Module Implementation Bugs](#04122025-report-module-bugs)\n"

# Find the table of contents section and insert new entry
toc_pattern = r'(# Mục Lục \(Table of Contents\)\n\n)'
replacement = r'\g<1>' + new_toc_entry

# Update numbering for existing entries
content = re.sub(toc_pattern, replacement, content)

# Update all subsequent numbering
lines = content.split('\n')
in_toc = False
toc_counter = 2
new_lines = []

for line in lines:
    if '# Mục Lục (Table of Contents)' in line:
        in_toc = True
        new_lines.append(line)
        continue
    
    if in_toc and line.startswith('---'):
        in_toc = False
        new_lines.append(line)
        continue
    
    if in_toc and re.match(r'^\d+\.', line.strip()):
        # Skip the new entry at position 1
        if toc_counter > 1:
            # Update numbering
            updated_line = re.sub(r'^\d+\.', f'{toc_counter}.', line.strip())
            new_lines.append(updated_line)
            toc_counter += 1
        else:
            toc_counter += 1
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

# Read the bug entry content
with open('backend/new_bug_entry.md', 'r', encoding='utf-8') as f:
    bug_entry = f.read()

# Find the position to insert (after the first ---) 
first_separator = content.find('\n---\n')
if first_separator != -1:
    # Insert after table of contents
    content = content[:first_separator + 5] + bug_entry + content[first_separator + 5:]

# Write back with UTF-8 encoding
with open('doc/Bug_Fixes_Documentation.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Successfully added bug entry with UTF-8 encoding!")
