import os
import json
import base64
import requests
from dotenv import load_dotenv

load_dotenv()


class AzureDevOpsClient:
    def __init__(self):
        org_name = os.getenv('AZURE_ORG_URL', '').strip('/')
        pat = os.getenv('PERSONAL_ACCESS_TOKEN')

        if not org_name or not pat:
            raise ValueError("Missing env variables: AZURE_ORG_URL and/or PERSONAL_ACCESS_TOKEN")

        self.base_url = f"https://dev.azure.com/{org_name}/_apis"

        # Basic Auth Header
        credentials = base64.b64encode(f":{pat}".encode("utf-8")).decode("utf-8")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Basic {credentials}"
        }

    def get_work_item_by_id(self, project, work_item_id):
        """Fetch a single work item directly by ID"""
        url = f"https://dev.azure.com/{os.getenv('AZURE_ORG_URL')}/{project}/_apis/wit/workitems/{work_item_id}?api-version=7.1"
        try:
            r = requests.get(url, headers=self.headers, verify=True)
            r.raise_for_status()
            item = r.json()
            item['attachments'] = self._process_attachments(project, work_item_id)
            return item
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch work item {work_item_id}: {e}")
            return None

    def get_work_items(self, query_params):
        """Fetch work items via WIQL (when ticket_id not provided)"""
        wiql_url = f"{self.base_url}/wit/wiql?api-version=7.1"
        query = {
            "query": f"""
            SELECT [System.Id]
            FROM WorkItems
            WHERE [System.TeamProject] = '{os.getenv('PROJECT_NAME')}'
            {"AND [System.AreaPath] = '{}'".format(os.getenv('AREA_PATH')) if os.getenv('AREA_PATH') else ''}
            {"AND [System.WorkItemType] = '{}'".format(os.getenv('WORK_ITEM_TYPE')) if os.getenv('WORK_ITEM_TYPE') else ''}
            {"AND [System.State] = '{}'".format(os.getenv('STATE')) if os.getenv('STATE') else ''}
            {"AND [System.AssignedTo] = '{}'".format(query_params.get('assigned_to')) if query_params.get('assigned_to') else ''}
            ORDER BY [System.ChangedDate] DESC
            """
        }

        try:
            r = requests.post(wiql_url, headers=self.headers, json=query, verify=True)
            r.raise_for_status()
            data = r.json()
            work_item_ids = [item['id'] for item in data.get('workItems', [])]
            return self._get_work_item_details(work_item_ids)
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] WIQL query failed: {e}")
            return []

    def _get_work_item_details(self, work_item_ids):
        """Batch fetch work item details"""
        if not work_item_ids:
            return []

        batch_url = f"{self.base_url}/wit/workitemsbatch?api-version=7.0"
        payload = {"ids": work_item_ids}
        try:
            r = requests.post(batch_url, headers=self.headers, json=payload, verify=True)
            r.raise_for_status()
            return r.json().get('value', [])
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get details: {e}")
            return []

    def _process_attachments(self, project, work_item_id):
        """Get attachments for a specific work item"""
        url = f"https://dev.azure.com/{os.getenv('AZURE_ORG_URL')}/{project}/_apis/wit/workitems/{work_item_id}/attachments?api-version=7.1"
        try:
            r = requests.get(url, headers=self.headers, verify=True)
            r.raise_for_status()
            return [{
                "id": att["id"],
                "url": att["url"],
                "name": att["attributes"]["name"],
                "size": att["attributes"].get("size", 0)
            } for att in r.json().get("value", [])]
        except requests.RequestException as e:
            print(f"[WARN] No attachments: {e}")
            return []


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract Azure DevOps work item details")
    parser.add_argument("--ticket-id", type=int, required=True)
    parser.add_argument("--project", type=str, required=True, help="Azure DevOps project name e.g. S2")
    args = parser.parse_args()

    client = AzureDevOpsClient()
    work_item = client.get_work_item_by_id(args.project, args.ticket_id)

    if work_item:
        output_dir = os.getenv("OUTPUT_DIR", "./output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"ticket_{args.ticket_id}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(work_item, f, indent=2)
        print(f"[SUCCESS] Saved ticket {args.ticket_id} to {output_path}")
    else:
        print(f"[INFO] Work item {args.ticket_id} not found")