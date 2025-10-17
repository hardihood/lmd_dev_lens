import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# Pull config
ORG_NAME = os.getenv('AZURE_ORG_URL', '').strip('/')
PAT = os.getenv('PERSONAL_ACCESS_TOKEN')

# Validation
if not ORG_NAME or not PAT:
    print("[ERROR] Missing required environment variables.")
    print("Required: AZURE_ORG_URL (org name only), PERSONAL_ACCESS_TOKEN")
    exit(1)

print(f"Using Azure DevOps Organization: {ORG_NAME}")
print(f"PAT detected: {'*' * len(PAT)}")

# Create Authorization header
credentials = base64.b64encode(f":{PAT}".encode("utf-8")).decode("utf-8")
headers = {
    "Accept": "application/json",
    "Authorization": f"Basic {credentials}"
}

# Test endpoint — work item 1 in your org/project
url = f"https://dev.azure.com/{ORG_NAME}/_apis/projects?api-version=7.0"

print("Testing PAT against Azure DevOps...")
response = requests.get(url, headers=headers, verify=True)

print(f"HTTP Status: {response.status_code}")
print("Content-Type:", response.headers.get("content-type"))

if response.status_code == 200:
    print("[SUCCESS] PAT is valid. Listing projects:")
    print(response.json())
else:
    print("[ERROR] PAT test failed.")
    with open('error.log', 'w', encoding='utf-8') as f:
        f.write(response.text or "No response content")