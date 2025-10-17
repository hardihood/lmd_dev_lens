import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class AzureDevOpsClient:
    def __init__(self):
        self.base_url = f"{os.getenv('AZURE_ORG_URL')}/_apis"
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Basic {os.getenv("PERSONAL_ACCESS_TOKEN")}'
        }
        
    def get_work_items(self, query_params):
        """Fetch work items based on WIQL query parameters"""
        wiql_url = f"{self.base_url}/wit/wiql?api-version=7.1"
        query = {
            "query": f"""
            SELECT [System.Id] 
            
            FROM WorkItems 
            WHERE [System.TeamProject] = '{os.getenv('PROJECT_NAME')}'
            AND [System.AreaPath] = '{os.getenv('AREA_PATH')}'
            AND [System.WorkItemType] = '{os.getenv('WORK_ITEM_TYPE')}'
            AND [System.State] = '{os.getenv('STATE')}'
            {"AND [System.AssignedTo] = '{}'".format(query_params.get('assigned_to')) if query_params.get('assigned_to') else ''}
            {"AND [System.Id] = {}".format(query_params.get('ticket_id')) if query_params.get('ticket_id') else ''}
            ORDER BY [System.ChangedDate] DESC
            """
        }
        
        try:
            response = requests.post(wiql_url, headers=self.headers, json=query)
            response.raise_for_status()
            work_item_ids = [item['id'] for item in response.json().get('workItems', [])]
            return self._get_work_item_details(work_item_ids)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching work items: {e}")
            return []

    def _get_work_item_details(self, work_item_ids):
        """Fetch detailed information for a list of work item IDs"""
        if not work_item_ids:
            return []
            
        batch_url = f"{self.base_url}/wit/workitems/{work_item_ids}?api-version=7.0"
        payload = {
            "ids": work_item_ids,
            "fields": [
                "System.Id", "System.Title", "System.Description",
                "System.AssignedTo", "System.State", "System.AreaPath",
                "System.Attachments"
            ]
        }
        
        try:
            response = requests.get(batch_url, headers=self.headers, verify=False)
            response.raise_for_status()
            items = response.json().get('value', [])
            
            for item in items:
                item['attachments'] = self._process_attachments(item.get('id'))
                
            return items
        except requests.exceptions.RequestException as e:
            print(f"Error fetching work item details: {e}")
            return []
            
    def _process_attachments(self, work_item_id):
        """Retrieve attachment metadata for a work item"""
        attachments_url = f"{self.base_url}/wit/workitems/{work_item_id}/attachments?api-version=7.1"
        try:
            response = requests.get(attachments_url, headers=self.headers)
            response.raise_for_status()
            return [{
                'id': att['id'],
                'url': att['url'],
                'name': att['attributes']['name'],
                'size': att['attributes']['size']
            } for att in response.json().get('value', [])]
        except requests.exceptions.RequestException as e:
            print(f"Error fetching attachments for work item {work_item_id}: {e}")
            return []

    def download_attachments(self, work_item_id, attachments):
        """Download all attachments for a work item"""
        output_dir = os.path.join(os.getenv('OUTPUT_DIR'), str(work_item_id))
        os.makedirs(output_dir, exist_ok=True)
        downloaded_files = []
        
        for attachment in attachments:
            file_path = os.path.join(output_dir, attachment['name'])
            try:
                # Get attachment content
                response = requests.get(
                    attachment['url'],
                    headers=self.headers,
                    stream=True
                )
                response.raise_for_status()
                
                # Save to file
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            
                downloaded_files.append(file_path)
                print(f"Downloaded {attachment['name']} to {file_path}")
                
            except requests.exceptions.RequestException as e:
                print(f"Failed to download {attachment['name']}: {e}")
            except IOError as e:
                print(f"File write error for {attachment['name']}: {e}")
                
        return downloaded_files

if __name__ == "__main__":
    print("Azure DevOps Ticket Extractor Module")
    client = AzureDevOpsClient()
    client._get_work_item_details(396712)
