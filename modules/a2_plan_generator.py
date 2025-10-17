import os
import yaml
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

class PlanGenerator:
    def __init__(self):
        self.llm_provider = os.getenv('LLM_PROVIDER')
        self.model_name = os.getenv('MODEL_NAME')
        self.output_dir = os.getenv('OUTPUT_PLAN_PATH')
        
    def generate_plan(self, ticket_data, additional_files=None):
        """Generate implementation plan using LLM"""
        try:
            # Prepare code context from additional files
            code_context = self._read_additional_files(additional_files)
            
            # Build and execute LLM prompt
            prompt = self._build_prompt(ticket_data, code_context)
            response = completion(
                model=f"{self.llm_provider}/{self.model_name}",
                messages=[{"content": prompt, "role": "user"}],
                temperature=0.2,
                max_tokens=2000
            )
            
            # Extract and validate YAML content
            plan_yaml = response.choices[0].message.content
            plan_data = yaml.safe_load(plan_yaml)
            
            # Save and return result
            return self._save_plan(plan_data, ticket_data['id'])
            
        except Exception as e:
            print(f"Plan generation failed: {e}")
            return None

    def _read_additional_files(self, files_dir):
        """Read and process additional context files"""
        if not files_dir or not os.path.isdir(files_dir):
            return {}
            
        code_context = {}
        for root, _, files in os.walk(files_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        code_context[os.path.relpath(file_path, files_dir)] = content
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        return code_context

    def _build_prompt(self, ticket_data, code_context):
        """Construct LLM prompt from ticket data and code context"""
        base_prompt = f"""You are an expert software engineer tasked with creating a detailed implementation plan for Azure DevOps ticket #{ticket_data['id']}.

**Ticket Details:**
- Title: {ticket_data.get('title', '')}
- Description: {ticket_data.get('description', '')}
- Attachments: {len(ticket_data.get('attachments', []))} files attached

**Codebase Context:**
{self._format_code_context(code_context)}

**Requirements:**
1. Create a step-by-step technical implementation plan
2. Identify specific files/classes to modify
3. Include test cases with assertions
4. Specify required database migrations
5. Outline rollout strategy with feature flags
6. Define metrics to capture

**Output Format (YAML):**
ticketId: {ticket_data['id']}
title: "[FEATURE] Short descriptive title"
branchName: "feature/{ticket_data['id']}-short-title"
problemStatement: "Clear description of the technical problem"
planSteps:
  - "Atomic technical action item"
targetFiles:
  - "path/to/modified_file.py"
testCases:
  - "tests/test_feature.py"
metricsToCapture:
  - "success_rate"
databaseChanges:
  - migrationScript: "db/migrations/YYYYMMDD_feature.sql"
featureFlags:
  - "enable_feature_name"
  
Return ONLY valid YAML, no markdown formatting."""
        return base_prompt

    def _format_code_context(self, code_context):
        """Format codebase context files for prompt"""
        if not code_context:
            return "No additional code context provided"
            
        context_str = "Codebase Overview:\n"
        for file_path, content in code_context.items():
            context_str += f"\n=== {file_path} ===\n{content[:1000]}\n..."
        return context_str

    def _save_plan(self, plan_data, ticket_id):
        """Save generated plan to YAML file"""
        required_fields = ['ticketId', 'title', 'planSteps', 'targetFiles']
        if not all(field in plan_data for field in required_fields):
            raise ValueError("Generated plan missing required fields")
            
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, f"plan_{ticket_id}.yaml")
        
        try:
            with open(output_path, 'w') as f:
                yaml.dump(plan_data, f, sort_keys=False)
            print(f"Plan saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Failed to save plan: {e}")
            return None

if __name__ == "__main__":
    print("Plan Generator Module")
