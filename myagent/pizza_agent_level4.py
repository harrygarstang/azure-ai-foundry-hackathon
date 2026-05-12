#!/usr/bin/env python3
"""
Level 4: Store Knowledge via File Search
- Uploads Contoso store markdown files into a vector store
- Attaches the FileSearch tool so the agent can answer store questions
- Updated instructions: agent must ask which store before confirming an order
"""

import os
import glob
from azure.identity import AzureCliCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FileSearchTool, FilePurpose

PROJECT_ENDPOINT = "https://harrys-resource.services.ai.azure.com/api/projects/harry-proj-default"
MODEL_DEPLOYMENT = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")
AGENT_NAME = "Level 4 Pizza Agent"
STORE_INFO_DIR = "store_info"
VECTOR_STORE_NAME = "contoso_pizza_stores"

INSTRUCTIONS = """\
You are an agent that helps customers order pizzas from Contoso Pizza.
You have a Gen-alpha personality, so you are friendly and helpful, but also a bit cheeky.

You have access to a knowledge base of Contoso Pizza retail stores (addresses,
opening hours, signature dishes, contact details). Use the file_search tool to
answer ANY question about specific stores — never guess. If a customer asks
about a city or location, search the store information.

You help customers order a pizza of their chosen size, crust, and toppings.
You don't like pineapple on pizzas, but you will help a customer order a pizza
with pineapple ... with some snark.

Before confirming any order, you MUST know:
1. The customer's name.
2. Which Contoso Pizza store they want to order from (suggest one based on
   their city if they don't know, using the file_search tool).

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
    """Reuse an existing vector store by name, or create a new one from .md files."""
    for vs in client.agents.vector_stores.list():
        if vs.name == name:
            print(f"♻️  Reusing existing vector store: {vs.id}")
            return vs

    md_paths = sorted(glob.glob(os.path.join(store_dir, "*.md")))
    if not md_paths:
        raise SystemExit(
            f"❌ No .md files found in {store_dir}/. "
            f"Put the Contoso store info files there first."
        )
    print(f"📄 Uploading {len(md_paths)} store files...")

    file_ids = []
    for p in md_paths:
        f = client.agents.files.upload_and_poll(file_path=p, purpose=FilePurpose.AGENTS)
        file_ids.append(f.id)
        print(f"   ✓ {os.path.basename(p)} -> {f.id}")

    print(f"🧠 Building vector store '{name}'...")
    vs = client.agents.vector_stores.create_and_poll(
        file_ids=file_ids,
        name=name,
    )
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
    print("=" * 60)
    print("🍕 Level 4: Pizza Agent — Store Knowledge")
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

        agent = project_client.agents.create_agent(
            model=MODEL_DEPLOYMENT,
            name=AGENT_NAME,
            instructions=INSTRUCTIONS,
            tools=file_search.definitions,
            tool_resources=file_search.resources,
        )
        print(f"✅ Agent created: {agent.id}")

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
                thread_id=thread.id, agent_id=agent.id
            )
            if run.status == "failed":
                print(f"❌ Run failed: {run.last_error}\n")
                continue

            reply = latest_assistant_reply(project_client, thread.id)
            print(f"Agent: {reply}\n")

        print(f"\n👋 Done. Agent stays in Foundry as '{AGENT_NAME}' ({agent.id}).")


if __name__ == "__main__":
    main()