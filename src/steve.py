"""
Steve Agent - Individual AI persona for bot-o'clock
Each Steve has its own personality, memory, voice, and LLM context
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import yaml
import os

from memory import MemoryStore, Message
from tts import VoiceProfile

logger = logging.getLogger(__name__)


@dataclass
class PersonaConfig:
    """Configuration for an agent's persona"""
    name: str
    system_prompt: str
    model: str = "llama3.1:8b"
    temperature: float = 0.7
    max_tokens: int = 2048
    goals: List[str] = field(default_factory=list)
    beliefs: List[str] = field(default_factory=list)
    traits: List[str] = field(default_factory=list)
    voice_sample: Optional[str] = None
    voice_language: str = "en"
    
    @staticmethod
    def from_yaml(file_path: str) -> 'PersonaConfig':
        """Load persona configuration from YAML file"""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return PersonaConfig(
            name=data['name'],
            system_prompt=data['system_prompt'],
            model=data.get('model', 'llama3.1:8b'),
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens', 2048),
            goals=data.get('goals', []),
            beliefs=data.get('beliefs', []),
            traits=data.get('traits', []),
            voice_sample=data.get('voice_sample'),
            voice_language=data.get('voice_language', 'en')
        )
    
    def to_yaml(self, file_path: str):
        """Save persona configuration to YAML file"""
        data = {
            'name': self.name,
            'system_prompt': self.system_prompt,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'goals': self.goals,
            'beliefs': self.beliefs,
            'traits': self.traits,
            'voice_sample': self.voice_sample,
            'voice_language': self.voice_language
        }
        
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)


class LLMClient:
    """
    Client for interacting with Ollama LLM
    """
    
    def __init__(self, host: str = "http://localhost:11434", timeout: int = 120):
        self.host = host
        self.timeout = timeout
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Send chat request to Ollama
        
        Args:
            model: Model name
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        try:
            import requests
            
            url = f"{self.host}/api/chat"
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result['message']['content']
            
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            return ""
    
    async def chat_async(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """Async version of chat"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.chat,
            model,
            messages,
            temperature,
            max_tokens
        )
    
    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            import requests
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class Steve:
    """
    Individual AI agent with persona, memory, and voice
    """
    
    def __init__(
        self,
        persona: PersonaConfig,
        memory_store: MemoryStore,
        llm_client: LLMClient,
        voice_profile: Optional[VoiceProfile] = None
    ):
        self.persona = persona
        self.memory = memory_store
        self.llm = llm_client
        self.voice = voice_profile
        
        # Current conversation
        self.conversation_id: Optional[int] = None
        self.context_messages: List[Message] = []
        self.max_context = 20
        
        # State
        self.is_active = False
        
        logger.info(f"Steve agent initialized: {persona.name}")
    
    def start_conversation(self, title: Optional[str] = None):
        """Start a new conversation"""
        self.conversation_id = self.memory.create_conversation(self.persona.name, title)
        self.context_messages = []
        self.is_active = True
        
        # Add system prompt to context
        system_msg = Message(
            role="system",
            content=self._build_system_prompt(),
            timestamp=datetime.utcnow().isoformat(),
            agent_name=self.persona.name
        )
        self.context_messages.append(system_msg)
        
        logger.info(f"Started conversation {self.conversation_id} for {self.persona.name}")
    
    def end_conversation(self):
        """End current conversation"""
        if self.conversation_id:
            self.memory.end_conversation(self.conversation_id)
            self.conversation_id = None
        self.is_active = False
    
    def _build_system_prompt(self) -> str:
        """Build the complete system prompt with persona details"""
        prompt_parts = [self.persona.system_prompt]
        
        if self.persona.goals:
            goals = "\n".join(f"- {goal}" for goal in self.persona.goals)
            prompt_parts.append(f"\nYour goals:\n{goals}")
        
        if self.persona.beliefs:
            beliefs = "\n".join(f"- {belief}" for belief in self.persona.beliefs)
            prompt_parts.append(f"\nYour beliefs:\n{beliefs}")
        
        if self.persona.traits:
            traits = ", ".join(self.persona.traits)
            prompt_parts.append(f"\nYour personality traits: {traits}")
        
        return "\n".join(prompt_parts)
    
    def process_input(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process user input and generate response
        
        Args:
            user_input: Text input from user
            context: Optional context information
            
        Returns:
            Agent's response text
        """
        if not self.conversation_id:
            self.start_conversation()
        
        # Create user message
        user_msg = Message(
            role="user",
            content=user_input,
            timestamp=datetime.utcnow().isoformat(),
            agent_name=None,  # User message
            metadata=context
        )
        
        # Add to context and save to memory
        self.context_messages.append(user_msg)
        self.memory.add_message(self.conversation_id, user_msg)
        
        # Prepare messages for LLM
        llm_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in self.context_messages[-self.max_context:]
        ]
        
        # Get response from LLM
        response = self.llm.chat(
            model=self.persona.model,
            messages=llm_messages,
            temperature=self.persona.temperature,
            max_tokens=self.persona.max_tokens
        )
        
        if not response:
            response = "I'm sorry, I couldn't process that. Could you try again?"
        
        # Create assistant message
        assistant_msg = Message(
            role="assistant",
            content=response,
            timestamp=datetime.utcnow().isoformat(),
            agent_name=self.persona.name
        )
        
        # Add to context and save to memory
        self.context_messages.append(assistant_msg)
        self.memory.add_message(self.conversation_id, assistant_msg)
        
        # Trim context if too large
        if len(self.context_messages) > self.max_context + 5:
            # Keep system message and recent messages
            system_msgs = [m for m in self.context_messages if m.role == "system"]
            recent_msgs = self.context_messages[-(self.max_context-1):]
            self.context_messages = system_msgs + recent_msgs
        
        logger.info(f"{self.persona.name} responded: {response[:100]}...")
        return response
    
    async def process_input_async(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Async version of process_input"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process_input, user_input, context)
    
    def load_history(self, message_limit: int = 20):
        """Load recent conversation history"""
        messages = self.memory.get_recent_messages(self.persona.name, message_limit)
        
        # Add system prompt
        system_msg = Message(
            role="system",
            content=self._build_system_prompt(),
            timestamp=datetime.utcnow().isoformat(),
            agent_name=self.persona.name
        )
        
        self.context_messages = [system_msg] + messages
        logger.info(f"Loaded {len(messages)} historical messages for {self.persona.name}")
    
    def clear_context(self):
        """Clear current context but keep system prompt"""
        system_msgs = [m for m in self.context_messages if m.role == "system"]
        self.context_messages = system_msgs
    
    def get_state(self) -> dict:
        """Get current agent state"""
        return {
            'name': self.persona.name,
            'model': self.persona.model,
            'conversation_id': self.conversation_id,
            'is_active': self.is_active,
            'context_size': len(self.context_messages)
        }
    
    def save_state(self):
        """Save agent state to memory"""
        state_data = {
            'persona': {
                'name': self.persona.name,
                'model': self.persona.model,
                'temperature': self.persona.temperature
            },
            'last_conversation_id': self.conversation_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.memory.save_agent_state(self.persona.name, state_data)
    
    def load_state(self):
        """Load agent state from memory"""
        state_data = self.memory.load_agent_state(self.persona.name)
        if state_data:
            self.conversation_id = state_data.get('last_conversation_id')
            logger.info(f"Loaded state for {self.persona.name}")
    
    def __repr__(self) -> str:
        return f"Steve(name={self.persona.name}, model={self.persona.model}, active={self.is_active})"


class SteveFactory:
    """
    Factory for creating Steve agents
    """
    
    def __init__(self, memory_store: MemoryStore, llm_client: LLMClient):
        self.memory = memory_store
        self.llm = llm_client
    
    def create_from_config(self, config_path: str) -> Steve:
        """
        Create Steve agent from configuration file
        
        Args:
            config_path: Path to persona YAML file
            
        Returns:
            Steve agent instance
        """
        persona = PersonaConfig.from_yaml(config_path)
        
        # Create voice profile if voice sample provided
        voice_profile = None
        if persona.voice_sample and os.path.exists(persona.voice_sample):
            voice_profile = VoiceProfile(
                name=persona.name,
                reference_audio=persona.voice_sample,
                language=persona.voice_language
            )
        
        return Steve(persona, self.memory, self.llm, voice_profile)
    
    def create_from_persona(self, persona: PersonaConfig, voice_profile: Optional[VoiceProfile] = None) -> Steve:
        """
        Create Steve agent from PersonaConfig object
        
        Args:
            persona: Persona configuration
            voice_profile: Optional voice profile
            
        Returns:
            Steve agent instance
        """
        return Steve(persona, self.memory, self.llm, voice_profile)


if __name__ == "__main__":
    # Test Steve agent
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Steve agent...")
    
    # Create test persona
    persona = PersonaConfig(
        name="TestSteve",
        system_prompt="You are a helpful AI assistant named Steve. You are friendly and knowledgeable.",
        model="llama3.1:8b",
        temperature=0.7,
        goals=["Be helpful", "Be informative"],
        beliefs=["Knowledge should be shared", "Kindness matters"],
        traits=["friendly", "patient", "curious"]
    )
    
    # Initialize components
    memory = MemoryStore("data/test_steve.db")
    llm = LLMClient()
    
    # Check Ollama connection
    if llm.check_connection():
        print("✓ Connected to Ollama")
    else:
        print("✗ Ollama not available (start with: ollama serve)")
    
    # Create Steve
    steve = Steve(persona, memory, llm)
    print(f"\nCreated agent: {steve}")
    print(f"System prompt: {steve._build_system_prompt()[:200]}...")
    
    print("\nSteve agent ready for interaction!")
