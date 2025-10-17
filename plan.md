🧠 PlanForge – Technical Implementation Plan
Overview

PlanForge automates extraction of Azure DevOps ticket data and generates detailed, LLM-assisted project-level implementation plans.
The system is designed to be run locally in Phase 1 and later deployable to cloud environments.
It supports multiple dev teams and repos, making it generic, configurable, and extensible.

🔹 Phase 1: Local Environment Setup (Windows)
1. System Requirements

OS: Windows 10 or later

Runtime: Python 3.10+

Package Manager: pip

Optional Tools: Git, VSCode, or any preferred IDE

2. Project Modules
Module	Description
A1 – Azure Ticket Data Extraction	Extracts work item data from Azure DevOps using REST APIs and stores it in structured JSON.
A2 – Project-Level Plan Creation	Consumes ticket data (and optional user files) to generate structured, LLM-assisted plan files using OpenAI via LiteLLM.
🧩 A1: Azure Ticket Data Extraction
1. Functionality

Extract work item details and attachments from Azure DevOps using WIQL (Work Item Query Language) based on user-defined filters.

2. Input Parameters
Variable	Description	Source
AZURE_ORG_URL	Azure DevOps organization URL	.env
PROJECT_NAME	Project name	.env
PERSONAL_ACCESS_TOKEN	PAT for authentication	.env
AREA_PATH	Area Path filter	.env
ASSIGNED_TO	Assigned user (optional)	User input
WORK_ITEM_TYPE	Type (e.g., User Story, Bug)	.env
STATE	Ticket state filter	.env
TICKET_ID	Ticket ID to extract	User input
OUTPUT_DIR	Local directory to store output JSON & attachments	.env
3. Steps

Authentication & Access

Use PAT-based authentication with Azure DevOps REST API.

Validate permissions for accessing work items.

Querying Work Items

Use WIQL API to query tickets using filters like AreaPath, AssignedTo, Type, and State.

Fetching Details & Attachments

For each ticket:

Extract fields: ID, Title, Description, AssignedTo, State, AreaPath.

Download attachments and save locally.

Output

Save all details into a structured JSON file, e.g.:

{
  "ticketId": 395683,
  "title": "Decanting of Totes",
  "description": "File for requirement in attachment.",
  "assignedTo": "User Name",
  "state": "Active",
  "attachments": ["./attachments/395683_req.docx"]
}

🧩 A2: Project-Level Plan File Creation (LLM Execution)
1. Functionality

Use the output JSON from A1, along with optional user-supplied files (e.g., README.md, PDFs, DOCX), to create a structured execution plan guiding developers to resolve the ticket.

2. Input Parameters
Variable	Description	Source
LLM_PROVIDER	Model provider (e.g., openai/gpt-4-turbo)	.env
LITELLM_API_KEY	Personal OpenAI key for LiteLLM	.env
MODEL_NAME	LLM model name	.env
TICKET_DATA_PATH	Path to JSON output from A1	User input
ADDITIONAL_FILES_DIR	Optional directory for user-supplied files	User input
OUTPUT_PLAN_PATH	Output path for plan file	.env
3. Steps

Input Handling

Read ticket JSON and user-supplied files.

Validate required fields before processing.

Analyze Ticket Description & Attachments

Use LiteLLM API (OpenAI backend) for summarization and requirement extraction.

Parse PDF/DOCX/text attachments for context.

Codebase Context Preparation

Expect multiple repositories under a single root directory.

Standard files to aid LLM understanding:

README.md
ARCHITECTURE.md
DESIGN.md
CONTRIBUTING.md
CODEBASE_OVERVIEW.md
CHANGELOG.md


LLM-Powered Planning

Prompt the model with ticket + repo context.

Generate plan including:

Problem statement

Sequential action steps

Files/classes to modify

Test cases and validation steps

Database migration details

Rollout and monitoring plan

Output Plan File (YAML Example)

ticketId: 395683
title: Decanting of Totes
branchName: feature/395683-decanting-totes
problemStatement: "Enable decanting functionality for totes."
planSteps:
  - Analyze current tote decanting flow in service class.
  - Modify `tote_service.py` to support decanting flag.
  - Add new unit tests in `tests/test_tote_decanting.py`.
  - Update config file `config/tote_config.yaml`.
  - Add feature flag `enable_tote_decanting` (default: false).
  - Apply migration script `db/migrations/2025_01_01_add_tote_decanting.sql`.
  - Deploy via phased rollout with daily metric checks.
targetFiles:
  - src/services/tote_service.py
  - config/tote_config.yaml
testCases:
  - tests/test_tote_decanting.py
metricsToCapture:
  - decantingSuccessRate
  - decantingFailureCount
databaseChanges:
  - migrationScript: db/migrations/2025_01_01_add_tote_decanting.sql
featureFlags:
  - enable_tote_decanting

⚙️ Configuration Management

All configuration values are centralized in .env file:

# Azure DevOps Config
AZURE_ORG_URL=https://dev.azure.com/landmarkgroup/
PROJECT_NAME=MDC-WMS-WCS
PERSONAL_ACCESS_TOKEN=<your_pat_here>

# Filters
AREA_PATH="MDC-WMS-WCS\\AreaName"
WORK_ITEM_TYPE="User Story"
STATE="Active"
OUTPUT_DIR="./output"

# LLM Config
LLM_PROVIDER=openai
MODEL_NAME=gpt-4-turbo
LITELLM_API_KEY=<your_openai_api_key>
OUTPUT_PLAN_PATH="./plans"


✅ Add .env to .gitignore to protect sensitive keys.

📘 README Additions (Phase 1)

Include in README.md:

### 🧠 PlanForge Local Setup

1. Clone the repository:
   ```bash
   git clone <repo_url>
   cd planforge


Create and configure .env file (refer to .env.example).

Install dependencies:

pip install -r requirements.txt


Run A1 module:

python a1_ticket_extractor.py --ticket-id 395683


Run A2 module:

python a2_plan_generator.py --input ./output/ticket_395683.json --additional ./user_files/


View the generated plan file in ./plans/.

🧩 Next Phase (Cloud Readiness)

Containerize the app using Docker.

Store configuration in Azure Key Vault or AWS Secrets Manager.

Expose A1 and A2 via REST APIs for remote access.

Integrate with CI/CD to auto-generate plan files for new tickets.