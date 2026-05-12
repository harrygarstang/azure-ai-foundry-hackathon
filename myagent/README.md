# Pizza Agent - Level 1

Create your first AI agent using Azure AI Foundry.

## Setup

The environment has been initialized with:
- Python virtual environment (`venv/`)
- Required dependencies installed:
  - `azure-identity` - Azure authentication
  - `azure-ai-projects` - Foundry Agent SDK
  - `semantic-kernel` - AI agent framework

## Running Your Agent

### Step 1: Authenticate with Azure

```bash
cd /workspaces/azure-ai-foundry-hackathon/myagent
source venv/bin/activate
az login --use-device-code
```

Follow the device code login instructions. This connects to your Azure subscription.

### Step 2: Create Your First Agent

```bash
python pizza_agent.py
```

This script will:
1. ✅ Authenticate using your Azure CLI credentials
2. ✅ Connect to your Azure AI Foundry project
3. ✅ Create a basic "hello world" agent
4. ✅ Test the agent with a sample message
5. ✅ Display your agent ID and next steps

## What Happens Next

After the script completes:

1. **Verify in Foundry Portal:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to your AI Foundry resource (`Harrys-resource`)
   - Find the "Agents" tab
   - Look for "Pizza Agent Level 1"

2. **Test in Agent Playground:**
   - Open the agent from the Agents tab
   - Click "Launch Playground"
   - Send it a message
   - It should respond with "hello"

## Troubleshooting

**Authentication Issue:**
```bash
az login --use-device-code
```

**Package Issues:**
```bash
pip install -r requirements.txt
```

**Connection Error:**
Make sure your subscription ID and resource group match:
- Subscription: `5398494a-a28d-4341-8927-e12f4f427992`
- Resource Group: `LabVM-RG`
- Project: `harry-proj-default`

## Next Steps

Once you've verified your agent works, proceed to **Level 2: Add Instructions & Persistent Memory** in the main hackathon instructions.
