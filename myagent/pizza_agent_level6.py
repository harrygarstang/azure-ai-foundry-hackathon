#!/usr/bin/env python3
"""
Level 6: Pizza MCP Server
- Keeps the Level 4 FileSearch (store knowledge) tool.
- Adds the Contoso Pizza MCP server so the agent can place real orders,
  check status, and cancel — which makes orders appear on the dashboard.
- Embeds the customer's Contoso Pizza user ID into the system prompt so
  the MCP server knows whose account the orders belong to.

>>> BEFORE RUNNING, FILL THE TWO VALUES IN THE TODO BLOCK BELOW <<<
"""

import os
import glob
from azure.identity import AzureCliCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FileSearchTool, FilePurpose, McpTool

# ---------------------------------------------------------------------------
# TODO: paste these two values from the hackathon instructors / Spektra VM
# ---------------------------------------------------------------------------
MCP_SERVER_URL = "https://ca-pizza-mcp-i77g52gdb73be.calmsmoke-e2439346.westus3.azurecontainerapps.io/mcp"
CONTOSO_USER_ID = "4fddbc20-4b21-4975-9ad1-0a7a070bb025"
# ---------------------------------------------------------------------------

PROJECT_ENDPOINT = "https://harrys-resource.services.ai.azure.com/api/projects/harry-proj-default"
MODEL_DEPLOYMENT = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")
AGENT_NAME = "Level 6 Pizza Agent"
STORE_INFO_DIR = "store_info"
VECTOR_STORE_NAME = "contoso_pizza_stores"
MCP_SERVER_LABEL = "contoso_pizza"

INSTRUCTIONS_TEMPLATE = """\
You are an agent that helps customers order pizzas from Contoso Pizza.
You have a Gen-alpha personality, so you are friendly and helpful, but also a bit cheeky.
You don't like pineapple on pizzas, but you will help a customer order pineapple
... with some snark.

You have TWO tools:

1. file_search — a knowledge base of Contoso Pizza retail stores (addresses,
   opening hours, signature dishes, contact details). Use this to answer ANY
   question about specific stores. Never guess.

2. The Contoso Pizza MCP server — use these tools to actually place orders,
   check their status, and cancel. ALWAYS use the MCP tools to place real
   orders. Do not just role-play taking an order.

The customer's Contoso Pizza user ID is: {user_id}
Use this user ID whenever an MCP tool requires it.

Before placing any order via the MCP server, you MUST know:
1. The customer's name.
2. Which Contoso Pizza store they want to order from (use file_search to
   suggest one based on their city if they don't know).
3. The size, crust, and toppings of each pizza they want.

After placing an order, tell the customer the order ID returned by the MCP
server so they know it went through.

You can't do anything except help customers order pizzas and give information
about Contoso Pizza. Politely deflect anything else.
"""


def cleanup_existing_agents(client, name):
    deleted = 0
    for agent in client.agents.list_agents():
        if agent.name == name:
            client.agents.delete_agent(agent.id)
            deleted += 1
    if deleted:
        print(f"🧹 Removed {deleted} existing agent(s) named '{name}'")


def find_or_create_vector_store(client, name, store_dir):
    for vs in client.agents.vector_stores.list():
        if vs.name == name:
            print(f"♻️  Reusing existing vector store: {vs.id}")
            return vs

    md_paths = sorted(glob.glob(os.path.join(store_dir, "*.md")))
    if not md_paths:
        raise SystemExit(f"❌ No .md files found in {store_dir}/.")
    print(f"📄 Uploading {len(md_paths)} store files...")

    file_ids = []
    for p in md_paths:
        f = client.agents.files.upload_and_poll(file_path=p, purpose=FilePurpose.AGENTS)
        file_ids.append(f.id)
        print(f"   ✓ {os.path.basename(p)} -> {f.id}")

    print(f"🧠 Building vector store '{name}'...")
    vs = client.agents.vector_stores.create_and_poll(file_ids=file_ids, name=name)
    print(f"✅ Vector store ready: {vs.id}")
    return vs


def latest_assistant_reply(client, thread_id):
    for msg in client.agents.messages.list(thread_id=thread_id):
        if msg.role == "assistant" and msg.content:
            for c in msg.content:
                if getattr(c, "text", None):
                    return c.text.value
    return None


def main():
    if not MCP_SERVER_URL or not CONTOSO_USER_ID:
        raise SystemExit(
            "❌ Fill MCP_SERVER_URL and CONTOSO_USER_ID at the top of this file first."
        )

    print("=" * 60)
    print("🍕 Level 6: Pizza Agent — MCP-powered orders")
    print("=" * 60)

    credential = AzureCliCredential()
    credential.get_token("https://management.azure.com/.default")
    project_client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)

    with project_client:
        cleanup_existing_agents(project_client, AGENT_NAME)

        vector_store = find_or_create_vector_store(
            project_client, VECTOR_STORE_NAME, STORE_INFO_DIR
        )
        file_search = FileSearchTool(vector_store_ids=[vector_store.id])

        mcp_tool = McpTool(
            server_label=MCP_SERVER_LABEL,
            server_url=MCP_SERVER_URL,
            allowed_tools=[],  # empty = expose every tool the server advertises
        )
        # Skip the human-approval step so runs don't hang on tool calls.
        mcp_tool.set_approval_mode("never")

        # Merge tool_resources so the agent has both FileSearch's vector store
        # AND MCP's per-server config (incl. approval-mode=never) baked in.
        merged_resources = {**file_search.resources, **mcp_tool.resources}

        agent = project_client.agents.create_agent(
            model=MODEL_DEPLOYMENT,
            name=AGENT_NAME,
            instructions=INSTRUCTIONS_TEMPLATE.format(user_id=CONTOSO_USER_ID),
            tools=file_search.definitions + mcp_tool.definitions,
            tool_resources=merged_resources,
        )
        print(f"✅ Agent created: {agent.id}")
        print(f"🔗 MCP server attached: {MCP_SERVER_URL}")

        thread = project_client.agents.threads.create()
        print(f"💬 Thread: {thread.id}")
        print("\nChat away. Type 'quit' to exit.\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input:
                continue
            if user_input.lower() in {"quit", "exit", "bye"}:
                break

            project_client.agents.messages.create(
                thread_id=thread.id, role="user", content=user_input
            )
            run = project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id,
            )
            if run.status == "failed":
                print(f"❌ Run failed: {run.last_error}\n")
                continue

            reply = latest_assistant_reply(project_client, thread.id)
            print(f"Agent: {reply}\n")

        print(f"\n👋 Done. Agent stays in Foundry as '{AGENT_NAME}' ({agent.id}).")


if __name__ == "__main__":
    main()
