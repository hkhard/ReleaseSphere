import requests
import json
import base64

class AzureDevOpsClient:

    def __init__(self, instance, collection, personal_access_token):
        self.instance = instance
        self.collection = collection
        self.personal_access_token = personal_access_token
        self.base_url = f"https://{instance}/{collection}"

    def _get_headers(self):
        auth = base64.b64encode(f":{self.personal_access_token}".encode()).decode()
        return {
            'Authorization': f'Basic {auth}',
            'Content-Type': 'application/json'
        }

    def get_all_projects(self):
        url = f"{self.base_url}/_apis/projects?api-version=7.0"
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code == 200:
            return response.json().get('value', [])
        return []

    def get_work_items(self, project, work_item_type):
        query = f"Select [System.Id] From WorkItems Where [System.WorkItemType] = '{work_item_type}' AND [System.TeamProject] = @project"
        url = f"{self.base_url}/{project}/_apis/wit/wiql?api-version=6.0"
        body = {"query": query}
        response = requests.post(url, json=body, headers=self._get_headers())
        
        if response.status_code == 200:
            work_item_refs = response.json().get('workItems', [])
            work_item_ids = [item['id'] for item in work_item_refs]
            
            if work_item_ids:
                work_items_url = f"{self.base_url}/{project}/_apis/wit/workitems?ids={','.join(map(str, work_item_ids))}&api-version=6.0"
                work_items_response = requests.get(work_items_url, headers=self._get_headers())
                
                if work_items_response.status_code == 200:
                    work_items = work_items_response.json().get('value', [])
                    return [{'id': item['id'], 'name': item['fields'].get('System.Title', ''), 'startDate': item['fields'].get('Microsoft.VSTS.Scheduling.StartDate', ''), 'endDate': item['fields'].get('Microsoft.VSTS.Scheduling.FinishDate', '')} for item in work_items]
        
        return []

    def get_sprints(self, project):
        url = f"{self.base_url}/{project}/_apis/work/teamsettings/iterations?api-version=6.0"
        response = requests.get(url, headers=self._get_headers())
        
        if response.status_code == 200:
            sprints = response.json().get('value', [])
            return [{'id': sprint['id'], 'name': sprint['name'], 'startDate': sprint.get('attributes', {}).get('startDate', ''), 'endDate': sprint.get('attributes', {}).get('finishDate', '')} for sprint in sprints]
        
        return []

    def test_connection(self):
        try:
            projects = self.get_all_projects()
            if projects:
                return True, f"Connection successful. Retrieved {len(projects)} projects."
            else:
                return False, "Failed to retrieve project information"
        except Exception as e:
            return False, f"Exception occurred: {str(e)}"
