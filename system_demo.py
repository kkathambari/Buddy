import asyncio
import os
import shutil
from typing import Dict, Any

from brain.ai_runtime.runtime import AIRuntimeManager, LLMRequest
from brain.ai_runtime.prompt_builder import PromptRequest
from brain.ai_runtime.providers.base_provider import BaseLLMProvider, ProviderResponse
from memory.knowledge_graph import KnowledgeGraphManager

# 1. We create a Mock Provider to simulate the Cloud LLM API (like GPT-4o or Claude)
#    so we don't have to wait for actual network calls in our demo.
class MockCloudProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__(provider_name="mock_gpt4o")

    async def generate(self, messages, model_id, temperature=0.7, max_tokens=2048, tools_schema=None):
        return ProviderResponse(
            text="Hello! Your current bonding level is HIGH. You recently unlocked the 'Night Owl' achievement.",
            raw_response={"mock": True},
            prompt_tokens=150,
            completion_tokens=40
        )

    async def stream(self, messages, model_id, temperature=0.7, max_tokens=2048, tools_schema=None):
        raise NotImplementedError()

import json

async def system_test():
    print("=== DEVBUDDY 2.0 E2E SYSTEM TEST ===")
    
    # Setup test directories
    db_dir = "tests/temp_demo_data"
    os.makedirs(db_dir, exist_ok=True)
    
    # 2. Initialize Memory (Knowledge Graph)
    print("\n[1] Initializing SQLite Knowledge Graph...")
    kg = KnowledgeGraphManager(db_path=f"{db_dir}/knowledge.db")
    kg.add_node("user_1", "User", json.dumps({"name": "Developer"}))
    
    # 3. Initialize AI Runtime Manager (The Centralized Gateway)
    print("[2] Initializing Centralized AI Runtime...")
    runtime = AIRuntimeManager(db_dir=db_dir)
    
    # Inject our mock provider into the runtime routing table
    mock_provider = MockCloudProvider()
    runtime.providers["openai"] = mock_provider
    runtime.providers["claude"] = mock_provider
    
    # 4. User asks a question
    user_question = "What is my current bonding level and achievements?"
    print(f"\n[3] User Question: '{user_question}'")
    
    # 5. Build prompt and send to AI Runtime
    print("[4] PromptBuilder layers context and ModelRouter selects provider...")
    req = LLMRequest(
        prompt_request=PromptRequest(
            user_message=user_question,
            memory_context=["User unlocked Night Owl achievement."],
            system_prompt="You are DevBuddy."
        ),
        task_hint="chat" # 'chat' hints the router to pick a specific model
    )
    
    # Execute the request through the runtime
    response = await runtime.execute(req)
    
    print(f"\n[5] AI Runtime Response (from '{response.provider_name}' via '{response.model_id}'):")
    print(f"    >> {response.text}")
    print(f"    >> (Tokens: {response.total_tokens}, Cached: {response.is_cached})")
    
    # 6. Save interaction to Memory Graph
    print("\n[6] Saving interaction to long-term memory...")
    kg.add_node("msg_1", "Message", json.dumps({"content": user_question, "role": "user"}))
    kg.add_node("msg_2", "Message", json.dumps({"content": response.text, "role": "assistant"}))
    kg.add_edge("msg_1", "msg_2", "REPLIED_TO")
    kg.add_edge("user_1", "msg_1", "ASKED")
    
    # 7. Verify memory storage
    print("\n[7] Verifying memory storage by querying SQLite Knowledge Graph...")
    messages = kg.get_related_nodes("user_1", "ASKED")
    print(f"    >> Found {len(messages)} messages asked by User stored permanently in SQLite.")
    for msg in messages:
        props = msg.get("properties", {})
        print(f"       - Message node '{msg['id']}': [{props.get('role', 'user')}] {props.get('content')}")
        
        # Check replies
        replies = kg.get_related_nodes(msg['id'], "REPLIED_TO")
        for reply in replies:
            r_props = reply.get("properties", {})
            print(f"       - Reply node '{reply['id']}': [{r_props.get('role', 'assistant')}] {r_props.get('content')}")
        
    # Cleanup
    shutil.rmtree(db_dir, ignore_errors=True)

if __name__ == "__main__":
    asyncio.run(system_test())
