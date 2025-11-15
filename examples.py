#!/usr/bin/env python3
"""
Example: Basic bot-o'clock usage
Demonstrates how to use bot-o'clock programmatically
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from memory import MemoryStore
from steve import LLMClient, SteveFactory, PersonaConfig
from stt import STTConfig, create_stt
from tts import TTSConfig, TTSManager
from orchestrator import Orchestrator


def example_basic_conversation():
    """Example: Basic conversation with a single agent"""
    print("="*60)
    print("Example 1: Basic Conversation")
    print("="*60)
    
    # Initialize components
    memory = MemoryStore("data/example_basic.db")
    llm = LLMClient()
    
    # Create a persona
    persona = PersonaConfig(
        name="ExampleSteve",
        system_prompt="You are a helpful assistant who loves to help with examples.",
        model="llama3.1:8b",
        temperature=0.7
    )
    
    # Create factory and agent
    factory = SteveFactory(memory, llm)
    steve = factory.create_from_persona(persona)
    
    # Start conversation
    steve.start_conversation("Example conversation")
    
    # Chat
    inputs = [
        "Hello! What's your name?",
        "Can you help me understand how you work?",
        "Thanks for the explanation!"
    ]
    
    for user_input in inputs:
        print(f"\nUser: {user_input}")
        response = steve.process_input(user_input)
        print(f"{steve.persona.name}: {response}")
    
    # End conversation
    steve.end_conversation()
    print("\n✓ Conversation ended\n")


def example_multiple_agents():
    """Example: Multiple agents with orchestrator"""
    print("="*60)
    print("Example 2: Multiple Agents")
    print("="*60)
    
    # Initialize components
    memory = MemoryStore("data/example_multi.db")
    llm = LLMClient()
    
    stt_config = STTConfig(model_size="base")
    stt = create_stt(stt_config, prefer_faster=False)  # Use fallback for demo
    
    tts_config = TTSConfig()
    try:
        tts_manager = TTSManager(tts_config)
    except:
        tts_manager = None  # TTS is optional
    
    factory = SteveFactory(memory, llm)
    
    # Create orchestrator
    orchestrator = Orchestrator(memory, stt, tts_manager, factory, max_agents=5)
    
    # Create multiple agents
    agents = [
        ("Alice", "assistant"),
        ("Bob", "creative"),
        ("Charlie", "default")
    ]
    
    for name, template in agents:
        steve = orchestrator.create_agent_from_template(name, template)
        print(f"✓ Created agent: {name} ({template})")
    
    # List agents
    print(f"\nAvailable agents: {orchestrator.list_agents()}")
    print(f"Active agent: {orchestrator.active_agent.persona.name}\n")
    
    # Interact with different agents
    commands = [
        ("Hello Alice!", None),
        ("Switch to Steve Bob", None),
        ("Tell me a creative story idea", None),
        ("Switch to Steve Charlie", None),
        ("What's the weather like?", None)
    ]
    
    for user_input, _ in commands:
        print(f"User: {user_input}")
        response = orchestrator.process_input(user_input)
        print(f"Response: {response}\n")
    
    orchestrator.stop()
    print("✓ Orchestrator stopped\n")


def example_inter_agent_conversation():
    """Example: Two agents talking to each other"""
    print("="*60)
    print("Example 3: Inter-Agent Conversation")
    print("="*60)
    
    # Initialize components
    memory = MemoryStore("data/example_inter.db")
    llm = LLMClient()
    
    # Create two agents with different personalities
    factory = SteveFactory(memory, llm)
    
    # Optimist
    optimist = factory.create_from_persona(PersonaConfig(
        name="Optimist",
        system_prompt="You are an eternal optimist. You see the bright side of everything.",
        temperature=0.8
    ))
    
    # Realist
    realist = factory.create_from_persona(PersonaConfig(
        name="Realist",
        system_prompt="You are a pragmatic realist. You focus on practical considerations.",
        temperature=0.6
    ))
    
    # Start conversations
    optimist.start_conversation("Discussion with Realist")
    realist.start_conversation("Discussion with Optimist")
    
    # Have them discuss a topic
    topic = "What do you think about the future of AI?"
    
    print(f"Topic: {topic}\n")
    
    message = topic
    for round in range(3):
        print(f"Round {round + 1}:")
        
        # Optimist responds
        opt_response = optimist.process_input(message)
        print(f"{optimist.persona.name}: {opt_response}")
        
        # Realist responds
        real_response = realist.process_input(opt_response)
        print(f"{realist.persona.name}: {real_response}\n")
        
        message = real_response
    
    optimist.end_conversation()
    realist.end_conversation()
    print("✓ Inter-agent conversation completed\n")


def example_memory_retrieval():
    """Example: Working with conversation memory"""
    print("="*60)
    print("Example 4: Memory Retrieval")
    print("="*60)
    
    memory = MemoryStore("data/example_memory.db")
    llm = LLMClient()
    
    factory = SteveFactory(memory, llm)
    persona = PersonaConfig(
        name="MemorySteve",
        system_prompt="You are a helpful assistant with good memory."
    )
    steve = factory.create_from_persona(persona)
    
    # First conversation
    steve.start_conversation("First chat")
    steve.process_input("My favorite color is blue")
    steve.process_input("I work as a software engineer")
    steve.end_conversation()
    
    print("✓ First conversation completed")
    
    # Second conversation - load history
    steve.start_conversation("Second chat")
    steve.load_history(message_limit=10)
    
    print(f"✓ Loaded {len(steve.context_messages)} messages from history")
    
    response = steve.process_input("What's my favorite color?")
    print(f"\nUser: What's my favorite color?")
    print(f"{steve.persona.name}: {response}")
    
    # Check conversation history
    conversations = memory.get_conversations(agent_name="MemorySteve")
    print(f"\n✓ Found {len(conversations)} conversation(s) in history")
    
    for conv in conversations:
        messages = memory.get_messages(conv.id)
        print(f"  Conversation {conv.id}: {len(messages)} messages")
    
    steve.end_conversation()
    print()


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("  bot-o'clock Usage Examples")
    print("="*60 + "\n")
    
    # Check Ollama
    from steve import LLMClient
    llm = LLMClient()
    
    if not llm.check_connection():
        print("⚠ Warning: Ollama is not running")
        print("  Start with: ollama serve")
        print("  Some examples may not work without Ollama\n")
    
    examples = [
        ("Basic Conversation", example_basic_conversation),
        ("Multiple Agents", example_multiple_agents),
        ("Inter-Agent Conversation", example_inter_agent_conversation),
        ("Memory Retrieval", example_memory_retrieval)
    ]
    
    for name, example_func in examples:
        try:
            example_func()
        except KeyboardInterrupt:
            print("\n\n⚠ Example interrupted by user\n")
            break
        except Exception as e:
            print(f"\n✗ Example failed: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("="*60)
    print("Examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
