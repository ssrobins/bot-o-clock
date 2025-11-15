"""
Orchestrator - Manages multiple Steve agents and audio routing
Coordinates multi-agent conversations and system commands
"""

import logging
import asyncio
from typing import Dict, Optional, List, Callable, Any
from dataclasses import dataclass
import re
import threading
import queue

from steve import Steve, SteveFactory, PersonaConfig
from audio_input import AudioInput, AudioConfig
from stt import WhisperSTT, STTConfig, StreamingTranscriber, create_stt
from tts import CoquiTTS, TTSConfig, AudioOutput, TTSManager
from memory import MemoryStore

logger = logging.getLogger(__name__)


@dataclass
class AudioRoute:
    """Represents audio routing configuration"""
    input_source: str  # 'microphone', 'file', 'virtual_device'
    target_agent: str
    output_device: Optional[int] = None


class VoiceCommandParser:
    """
    Parse voice commands for system control
    """
    
    # Command patterns
    PATTERNS = {
        'create_agent': r"create (?:a )?new steve (?:named |called )?([a-zA-Z0-9_]+)",
        'switch_agent': r"switch to steve ([a-zA-Z0-9_]+)",
        'list_agents': r"list (?:all )?(?:steve)?(?:s)?(?:agents)?",
        'agent_talk': r"let (?:steve )?([a-zA-Z0-9_]+) and (?:steve )?([a-zA-Z0-9_]+) talk",
        'stop_agent': r"stop (?:steve )?([a-zA-Z0-9_]+)",
        'exit': r"exit (?:bot[- ]?o[- ]?clock)?",
        'help': r"(?:help|what can you do)"
    }
    
    @classmethod
    def parse(cls, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse text for voice commands
        
        Args:
            text: Input text
            
        Returns:
            Command dictionary or None
        """
        text = text.lower().strip()
        
        for command_type, pattern in cls.PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result = {
                    'type': command_type,
                    'raw_text': text
                }
                
                # Extract parameters based on command type
                if command_type == 'create_agent':
                    result['name'] = match.group(1)
                elif command_type == 'switch_agent':
                    result['name'] = match.group(1)
                elif command_type == 'stop_agent':
                    result['name'] = match.group(1)
                elif command_type == 'agent_talk':
                    result['agent1'] = match.group(1)
                    result['agent2'] = match.group(2)
                
                return result
        
        return None


class Orchestrator:
    """
    Manages multiple Steve agents, audio routing, and inter-agent communication
    """
    
    def __init__(
        self,
        memory_store: MemoryStore,
        stt: WhisperSTT,
        tts_manager: TTSManager,
        steve_factory: SteveFactory,
        max_agents: int = 10
    ):
        self.memory = memory_store
        self.stt = stt
        self.tts_manager = tts_manager
        self.steve_factory = steve_factory
        self.max_agents = max_agents
        
        # Agent management
        self.agents: Dict[str, Steve] = {}
        self.active_agent: Optional[Steve] = None
        
        # Audio routing
        self.audio_inputs: Dict[str, AudioInput] = {}
        self.audio_outputs: Dict[str, AudioOutput] = {}
        self.routes: List[AudioRoute] = []
        
        # System state
        self.is_running = False
        self.command_queue = queue.Queue()
        
        logger.info("Orchestrator initialized")
    
    def add_agent(self, steve: Steve) -> bool:
        """
        Add a Steve agent to the orchestrator
        
        Args:
            steve: Steve agent instance
            
        Returns:
            True if successful
        """
        if len(self.agents) >= self.max_agents:
            logger.warning(f"Maximum number of agents ({self.max_agents}) reached")
            return False
        
        if steve.persona.name in self.agents:
            logger.warning(f"Agent {steve.persona.name} already exists")
            return False
        
        self.agents[steve.persona.name] = steve
        
        # Add voice profile if available
        if steve.voice:
            self.tts_manager.add_voice_profile(steve.voice)
        
        # Set as active if no active agent
        if not self.active_agent:
            self.active_agent = steve
        
        logger.info(f"Added agent: {steve.persona.name}")
        return True
    
    def remove_agent(self, name: str) -> bool:
        """Remove an agent"""
        if name not in self.agents:
            logger.warning(f"Agent {name} not found")
            return False
        
        agent = self.agents[name]
        agent.end_conversation()
        
        # Remove voice profile
        if agent.voice:
            self.tts_manager.remove_voice_profile(name)
        
        del self.agents[name]
        
        # Update active agent if needed
        if self.active_agent == agent:
            self.active_agent = next(iter(self.agents.values())) if self.agents else None
        
        logger.info(f"Removed agent: {name}")
        return True
    
    def switch_agent(self, name: str) -> bool:
        """Switch to a different active agent"""
        if name not in self.agents:
            logger.warning(f"Agent {name} not found")
            return False
        
        self.active_agent = self.agents[name]
        logger.info(f"Switched to agent: {name}")
        return True
    
    def get_agent(self, name: str) -> Optional[Steve]:
        """Get agent by name"""
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """Get list of all agent names"""
        return list(self.agents.keys())
    
    def create_agent_from_template(
        self,
        name: str,
        template: str = "default",
        voice_sample: Optional[str] = None
    ) -> Optional[Steve]:
        """
        Create a new agent from a template
        
        Args:
            name: Name for the new agent
            template: Template type ('default', 'assistant', 'creative')
            voice_sample: Optional voice sample path
            
        Returns:
            Created Steve agent or None
        """
        # Define templates
        templates = {
            'default': {
                'system_prompt': f"You are {name}, a helpful AI assistant. You are friendly, knowledgeable, and eager to help.",
                'goals': ["Be helpful", "Be informative", "Be engaging"],
                'beliefs': ["Knowledge should be shared", "Respect others", "Stay curious"],
                'traits': ["friendly", "patient", "knowledgeable"]
            },
            'assistant': {
                'system_prompt': f"You are {name}, a professional AI assistant. You are efficient, accurate, and detail-oriented.",
                'goals': ["Provide accurate information", "Be efficient", "Stay professional"],
                'beliefs': ["Accuracy is crucial", "Time is valuable", "Clarity matters"],
                'traits': ["professional", "organized", "precise"]
            },
            'creative': {
                'system_prompt': f"You are {name}, a creative AI companion. You are imaginative, playful, and love brainstorming ideas.",
                'goals': ["Inspire creativity", "Think outside the box", "Have fun"],
                'beliefs': ["Creativity is essential", "No idea is bad", "Imagination matters"],
                'traits': ["creative", "playful", "enthusiastic"]
            }
        }
        
        template_data = templates.get(template, templates['default'])
        
        persona = PersonaConfig(
            name=name,
            system_prompt=template_data['system_prompt'],
            goals=template_data['goals'],
            beliefs=template_data['beliefs'],
            traits=template_data['traits'],
            voice_sample=voice_sample
        )
        
        steve = self.steve_factory.create_from_persona(persona)
        
        if self.add_agent(steve):
            return steve
        return None
    
    def process_voice_command(self, text: str) -> str:
        """
        Process voice commands for system control
        
        Args:
            text: Transcribed voice input
            
        Returns:
            Response message
        """
        command = VoiceCommandParser.parse(text)
        
        if not command:
            # Not a system command, pass to active agent
            return None
        
        logger.info(f"Processing command: {command['type']}")
        
        if command['type'] == 'create_agent':
            name = command['name']
            agent = self.create_agent_from_template(name)
            if agent:
                return f"Created new agent: {name}"
            return f"Failed to create agent: {name}"
        
        elif command['type'] == 'switch_agent':
            name = command['name']
            if self.switch_agent(name):
                return f"Switched to {name}"
            return f"Agent {name} not found"
        
        elif command['type'] == 'list_agents':
            agents = self.list_agents()
            if agents:
                agent_list = ", ".join(agents)
                active = self.active_agent.persona.name if self.active_agent else "none"
                return f"Available agents: {agent_list}. Active agent: {active}"
            return "No agents available"
        
        elif command['type'] == 'stop_agent':
            name = command['name']
            if self.remove_agent(name):
                return f"Stopped agent: {name}"
            return f"Agent {name} not found"
        
        elif command['type'] == 'agent_talk':
            agent1 = command['agent1']
            agent2 = command['agent2']
            response = self.initiate_inter_agent_conversation(agent1, agent2)
            return response
        
        elif command['type'] == 'exit':
            self.stop()
            return "Shutting down bot-o'clock. Goodbye!"
        
        elif command['type'] == 'help':
            return self._get_help_text()
        
        return None
    
    def process_input(self, text: str) -> str:
        """
        Process text input through active agent or as command
        
        Args:
            text: Input text
            
        Returns:
            Response text
        """
        # Check for system command first
        command_response = self.process_voice_command(text)
        if command_response:
            return command_response
        
        # Pass to active agent
        if self.active_agent:
            return self.active_agent.process_input(text)
        
        return "No active agent. Create an agent first."
    
    def initiate_inter_agent_conversation(
        self,
        agent1_name: str,
        agent2_name: str,
        topic: str = "Hello",
        rounds: int = 3
    ) -> str:
        """
        Facilitate conversation between two agents
        
        Args:
            agent1_name: First agent name
            agent2_name: Second agent name
            topic: Initial topic
            rounds: Number of conversation rounds
            
        Returns:
            Status message
        """
        agent1 = self.get_agent(agent1_name)
        agent2 = self.get_agent(agent2_name)
        
        if not agent1 or not agent2:
            return f"One or both agents not found"
        
        logger.info(f"Starting conversation between {agent1_name} and {agent2_name}")
        
        # Start conversations
        if not agent1.conversation_id:
            agent1.start_conversation(f"Conversation with {agent2_name}")
        if not agent2.conversation_id:
            agent2.start_conversation(f"Conversation with {agent1_name}")
        
        # Initial message
        message = topic
        
        # Exchange messages
        for i in range(rounds):
            # Agent 1 responds
            response1 = agent1.process_input(message, context={'inter_agent': True, 'other_agent': agent2_name})
            logger.info(f"{agent1_name}: {response1[:100]}...")
            
            # Agent 2 responds
            response2 = agent2.process_input(response1, context={'inter_agent': True, 'other_agent': agent1_name})
            logger.info(f"{agent2_name}: {response2[:100]}...")
            
            message = response2
        
        return f"Completed {rounds} rounds of conversation between {agent1_name} and {agent2_name}"
    
    def add_audio_input(self, name: str, config: AudioConfig) -> AudioInput:
        """Add an audio input source"""
        audio_input = AudioInput(config)
        self.audio_inputs[name] = audio_input
        logger.info(f"Added audio input: {name}")
        return audio_input
    
    def add_audio_output(self, name: str, device: Optional[int] = None) -> AudioOutput:
        """Add an audio output device"""
        audio_output = AudioOutput(device=device)
        self.audio_outputs[name] = audio_output
        logger.info(f"Added audio output: {name}")
        return audio_output
    
    def add_route(self, route: AudioRoute):
        """Add an audio routing configuration"""
        self.routes.append(route)
        logger.info(f"Added route: {route.input_source} -> {route.target_agent}")
    
    def start(self):
        """Start the orchestrator"""
        self.is_running = True
        logger.info("Orchestrator started")
    
    def stop(self):
        """Stop the orchestrator"""
        self.is_running = False
        
        # End all agent conversations
        for agent in self.agents.values():
            agent.end_conversation()
        
        # Stop audio inputs
        for audio_input in self.audio_inputs.values():
            audio_input.stop_recording()
        
        logger.info("Orchestrator stopped")
    
    def _get_help_text(self) -> str:
        """Get help text for voice commands"""
        return """
Available voice commands:
- "Create a new Steve named [name]" - Create a new agent
- "Switch to Steve [name]" - Switch active agent
- "List agents" - Show all agents
- "Let [agent1] and [agent2] talk" - Start inter-agent conversation
- "Stop [agent]" - Remove an agent
- "Exit bot-o'clock" - Shut down the system
- "Help" - Show this help message
"""
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'running': self.is_running,
            'agents': len(self.agents),
            'active_agent': self.active_agent.persona.name if self.active_agent else None,
            'audio_inputs': len(self.audio_inputs),
            'audio_outputs': len(self.audio_outputs),
            'routes': len(self.routes)
        }


if __name__ == "__main__":
    # Test orchestrator
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Orchestrator...")
    
    # Initialize components
    from steve import LLMClient
    
    memory = MemoryStore("data/test_orchestrator.db")
    llm = LLMClient()
    
    stt_config = STTConfig(model_size="base")
    stt = create_stt(stt_config)
    
    tts_config = TTSConfig()
    tts_manager = TTSManager(tts_config)
    
    factory = SteveFactory(memory, llm)
    
    # Create orchestrator
    orchestrator = Orchestrator(memory, stt, tts_manager, factory, max_agents=5)
    
    # Create test agents
    agent1 = orchestrator.create_agent_from_template("Alice", "assistant")
    agent2 = orchestrator.create_agent_from_template("Bob", "creative")
    
    print(f"\nCreated agents: {orchestrator.list_agents()}")
    print(f"Active agent: {orchestrator.active_agent.persona.name if orchestrator.active_agent else 'None'}")
    
    # Test command parsing
    commands = [
        "create a new steve named Charlie",
        "switch to steve Bob",
        "list all agents",
        "let Alice and Bob talk",
        "exit bot-o'clock"
    ]
    
    print("\nTesting voice commands:")
    for cmd in commands:
        parsed = VoiceCommandParser.parse(cmd)
        print(f"  '{cmd}' -> {parsed['type'] if parsed else 'Not a command'}")
    
    print("\nOrchestrator ready!")
