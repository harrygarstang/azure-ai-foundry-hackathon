#!/usr/bin/env python3
"""
Level 1: Create Your First Agent
A basic "hello world" agent using Azure AI Foundry
"""

import os
import sys
import time
from azure.identity import AzureCliCredential
from azure.ai.projects import AIProjectClient


def authenticate_with_azure():
    """
    Authenticate using Azure CLI credentials.
    Make sure you've run: az login --use-device-code
    """
    try:
        credential = AzureCliCredential()
        # Test credentials by getting token
        token = credential.get_token("https://management.azure.com/.default")
        print("✅ Successfully authenticated with Azure CLI")
        return credential
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("Run: az login --use-device-code")
        sys.exit(1)


def create_hello_agent(client, agent_name="Pizza Agent Level 1"):
    """
    Create a basic agent that responds with "hello"
    """
    try:
        print(f"\n📋 Creating agent: {agent_name}")
        
        # Create the agent using the OpenAI client through the project
        openai_client = client.get_openai_client()
        
        agent = openai_client.beta.assistants.create(
            name=agent_name,
            instructions="You are a helpful assistant. Always respond with 'hello' to any user input.",
            model="gpt-4o"
        )
        
        print(f"✅ Agent created successfully!")
        print(f"   Agent ID: {agent.id}")
        print(f"   Agent Name: {agent.name}")
        return agent
        
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        print(f"   Make sure you have a deployed GPT-4o model in your Foundry project")
        sys.exit(1)


def test_agent(client, agent):
    """
    Test the agent by sending a message and checking the response
    """
    try:
        print(f"\n🧪 Testing agent...")
        
        openai_client = client.get_openai_client()
        
        # Create a new thread
        thread = openai_client.beta.threads.create()
        print(f"   Created thread: {thread.id}")
        
        # Send a message
        message = openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Hello, are you there?"
        )
        print(f"   Sent message: 'Hello, are you there?'")
        
        # Create a run
        run = openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=agent.id
        )
        print(f"   Created run: {run.id}")
        
        # Wait for completion
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            run = openai_client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run.status == "completed":
                break
            elif run.status == "failed":
                print(f"❌ Run failed with error: {run.last_error}")
                return False
            attempt += 1
            time.sleep(1)
        
        if attempt >= max_attempts:
            print(f"⏱️  Run timed out after {max_attempts} seconds")
            return False
        
        # Get response messages
        messages = openai_client.beta.threads.messages.list(thread_id=thread.id)
        response_messages = [m for m in messages.data if m.role == "assistant"]
        
        if response_messages:
            response = response_messages[0].content[0].text.value
            print(f"✅ Agent response: '{response}'")
            return True
        else:
            print(f"❌ No response from agent")
            return False
            
    except Exception as e:
        print(f"⚠️  Test failed (don't worry, your agent is created): {e}")
        return False


def main():
    """Main function to orchestrate agent creation"""
    
    print("=" * 60)
    print("🍕 Level 1: Create Your First Agent")
    print("=" * 60)
    
    # Step 1: Authenticate
    print("\n1️⃣  Authenticating with Azure CLI...")
    credential = authenticate_with_azure()
    
    # Step 2: Connect to Foundry
    print("\n2️⃣  Connecting to Azure AI Foundry...")
    try:
        client = AIProjectClient(
            credential=credential,
            subscription_id="5398494a-a28d-4341-8927-e12f4f427992",  # Your subscription
            resource_group_name="LabVM-RG",
            project_name="harry-proj-default",
            endpoint="https://harrys-resource.services.ai.azure.com/"
        )
        print("✅ Connected to Foundry successfully")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        sys.exit(1)
    
    # Step 3: Create the agent
    print("\n3️⃣  Creating agent...")
    agent = create_hello_agent(client)
    
    # Step 4: Test the agent
    print("\n4️⃣  Testing agent...")
    test_agent(client, agent)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ LEVEL 1 COMPLETE!")
    print("=" * 60)
    print(f"\n🎉 Your agent '{agent.name}' is ready!")
    print(f"\n📍 Next steps:")
    print(f"   1. Go to Microsoft Foundry Portal")
    print(f"   2. Navigate to Agents tab")
    print(f"   3. Find '{agent.name}' in your list")
    print(f"   4. Test it in the Agent Playground")
    print(f"\n🚀 When ready, proceed to Level 2: Add Instructions & Persistent Memory")
    print("=" * 60)


if __name__ == "__main__":
    main()
