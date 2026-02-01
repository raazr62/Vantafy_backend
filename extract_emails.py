import glob
import re
import json
import os

# Use raw string for Windows path
spiders_dir = r'c:\Users\Rafi\django_projects\fixing\media_extraction_hub\media_extraction_hub\spiders\*.py'
data = []

files = glob.glob(spiders_dir)
# print(f"Found {len(files)} files")

for file_path in files:
    if '__init__' in file_path: continue
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            name_match = re.search(r'name\s*=\s*[\"\'](.+?)[\"\']', content)
            emails_match = re.search(r'emails\s*=\s*\[(.*?)\]', content, re.DOTALL)
            
            if name_match:
                website = name_match.group(1)
                email = ''
                if emails_match:
                    # Extract first email strings
                    email_str = emails_match.group(1)
                    # Find all strings in the list
                    found_emails = re.findall(r'[\"\'](.+?)[\"\']', email_str)
                    if found_emails:
                        email = found_emails[0]
                
                # Only add if we have both website and email (or just website?)
                # User asked for both.
                if website and email:
                    data.append({'website': website, 'email': email})
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

print(json.dumps(data, indent=4))
