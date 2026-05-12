#!/usr/bin/env python3
"""
Level 1: Create Your First Agent
Foundry-native version (no Azure-OpenAI Assistants path)
"""

import os
import sys
from azure.identity import AzureCliCredential
from azure.ai.projects import AIProjectClient

# Full project endpoint format: https://<resource>.services.ai.azure.com/api/projects/<project>
PROJECT_ENDPOINT = "https://harrys-resource.services.ai.azure.com/api/projects/harry-proj-default"

# IMPORTANT: this must match the DEPLOYMENT NAME in Foundry > Models + Endpoints,
# not just the model family. Check in the portal — it might be "gpt-4o", "gpt-4o-mini", etc.
MODEL_DEPLOYMENT = os.environ.get("MODEL_DEPLOYMENT_NAME", "gpt-4o")


def main():
    print("=" * 60)
    print("🍕 Level 1: Create Your First Agent")
    print("=" * 60)

    print("\n1️⃣  Authenticating with Azure CLI...")
    credential = AzureCliCredential()
    credential.get_token("https://management.azure.com/.default")  # fail fast if not logged in
    print("✅ Authenticated")

    print("\n2️⃣  Connecting to Foundry project...")
    project_client = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credential)

    with project_client:
        print("✅ Connected")

        print("\n3️⃣  Creating agent...")
        agent = project_client.agents.create_agent(
            model=MODEL_DEPLOYMENT,
            name="Pizza Agent Level 1",
            instructions="You are a helpful assistant. Always respond with 'hello' to any user input.",
        )
        print(f"✅ Agent ID: {agent.id}")
        print(f"   Name:    {agent.name}")

        print("\n4️⃣  Testing agent...")
        thread = project_client.agents.threads.create()
        print(f"   Thread: {thread.id}")

        project_client.agents.messages.create(
            thread_id=thread.id,
            role="user",
            content="Hello, are you there?",
        )

        run = project_client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=agent.id,
        )
        print(f"   Run status: {run.status}")

        if run.status == "failed":
            print(f"❌ Run failed: {run.last_error}")
            sys.exit(1)

        # Most recent assistant message
        for msg in project_client.agents.messages.list(thread_id=thread.id):
            if msg.role == "assistant" and msg.content:
                for c in msg.content:
                    if getattr(c, "text", None):
                        print(f"✅ Agent response: {c.text.value}")
                        break
                break

    print("\n" + "=" * 60)
    print("✅ LEVEL 1 COMPLETE — check the Agents tab in Foundry portal")
    print("=" * 60)


if __name__ == "__main__":
    main()