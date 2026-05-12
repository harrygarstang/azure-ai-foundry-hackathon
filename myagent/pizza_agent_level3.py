#!/usr/bin/env python3
"""
Level 3: Personality + Persistent Memory
- Custom instructions give the agent a Contoso Pizza personality
- A single thread is reused across turns -> agent remembers the customer's name
- Existing agents with the same name are deleted on re-run to keep Foundry tidy
"""

import os
from azure.identity import AzureCliCredential
from azure.ai.projects import AIProjectClient

PROJECT_ENDPOINT = "https://harrys-resource.services.ai.azure.com/api/projects/harry-proj-default"
MODEL_DEPLOYMENT = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")
AGENT_NAME = "Level 3 Pizza Agent"

INSTRUCTIONS = """\
You are an agent that helps customers order pizzas from Contoso Pizza.
You have a Gen-alpha personality, so you are friendly and helpful, but also a bit cheeky.
You can provide information about Contoso Pizza and its retail stores.
You help customers order a pizza of their chosen size, crust, and toppings.
You don't like pineapple on pizzas, but you will help a customer order a pizza
with pineapple ... with some snark.
Make sure you know the customer's name before placing an order on their behalf.
You can't do anything except help customers order pizzas and give information
about Contoso Pizza. You will gently deflect any other questions.
"""


def cleanup_existing_agents(client, name):
    """Delete any existing agents with the same name."""
    deleted = 0
    # In azure-ai-projects 1.0.0 this is `list_agents`. If your installed version
    # complains, swap to `client.agents.list()`.
    for agent in client.agents.list_agents():
        if agent.name == name:
            client.agents.delete_agent(agent.id)
            deleted += 1
    if deleted:
        print(f"🧹 Removed {deleted} existing agent(s) named '{name}'")


def latest_assistant_reply(client, thread_id):
    """Return the most recent assistant message text on a thread."""
    for msg in client.agents.messages.list(thread_id=thread_id):
        if msg.role == "assistant" and msg.content:
            for c in msg.content:
                if getattr(c, "text", None):
                    return c.text.value
    return None


def main():
    print("=" * 60)
    print("🍕 Level 3: Pizza Agent — Personality + Memory")
    print("=" * 60)

    credential = AzureCliCredential()
    credential.get_token("https://management.azure.com/.default")

    project_client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)

    with project_client:
        cleanup_existing_agents(project_client, AGENT_NAME)

        agent = project_client.agents.create_agent(
            model=MODEL_DEPLOYMENT,
            name=AGENT_NAME,
            instructions=INSTRUCTIONS,
        )
        print(f"✅ Agent created: {agent.id}")

        # ONE thread for the whole chat session — this is the memory.
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
                thread_id=thread.id,
                role="user",
                content=user_input,
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