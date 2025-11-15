"""
bot-o'clock - Main entry point
Local, voice-driven, multi-agent AI persona framework
"""

import sys
import os
import logging
import asyncio
import signal
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from audio_input import AudioInput, AudioConfig
from stt import WhisperSTT, STTConfig, StreamingTranscriber, create_stt
from tts import CoquiTTS, TTSConfig, AudioOutput, TTSManager
from memory import MemoryStore
from steve import Steve, SteveFactory, LLMClient, PersonaConfig
from orchestrator import Orchestrator

console = Console()
logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration"""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                show_time=False,
                show_path=False
            )
        ]
    )
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(file_handler)


def load_config(config_path: str = "config/settings.yaml") -> dict:
    """Load configuration from YAML file"""
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class BotOClock:
    """
    Main application class for bot-o'clock
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.orchestrator: Optional[Orchestrator] = None
        self.audio_input: Optional[AudioInput] = None
        self.audio_output: Optional[AudioOutput] = None
        self.streaming_transcriber: Optional[StreamingTranscriber] = None
        self.running = False
        
    def initialize(self):
        """Initialize all components"""
        console.print(Panel.fit(
            "[bold cyan]🕒 bot-o'clock[/bold cyan]\n"
            "[dim]Local Voice-Driven Multi-Agent AI Framework[/dim]",
            border_style="cyan"
        ))
        
        console.print("\n[yellow]Initializing components...[/yellow]")
        
        # Memory store
        memory_config = self.config.get('memory', {})
        db_path = memory_config.get('db_path', 'data/memories.db')
        memory = MemoryStore(db_path)
        console.print("✓ Memory store initialized")
        
        # LLM client
        llm_config = self.config.get('llm', {})
        llm_host = llm_config.get('host', 'http://localhost:11434')
        llm = LLMClient(host=llm_host)
        
        # Check Ollama connection
        if llm.check_connection():
            console.print("✓ Connected to Ollama")
        else:
            console.print("[red]✗ Ollama not running. Start with: ollama serve[/red]")
            console.print("[yellow]  Some features will not work without Ollama[/yellow]")
        
        # STT
        stt_config_data = self.config.get('stt', {})
        stt_config = STTConfig(
            model_size=stt_config_data.get('model', 'base'),
            language=stt_config_data.get('language', 'en'),
            device=stt_config_data.get('device', 'cpu'),
            compute_type=stt_config_data.get('compute_type', 'int8')
        )
        stt = create_stt(stt_config)
        console.print(f"✓ Speech-to-text loaded (Whisper {stt_config.model_size})")
        
        # TTS
        tts_config_data = self.config.get('tts', {})
        tts_config = TTSConfig(
            model_name=tts_config_data.get('model', 'tts_models/multilingual/multi-dataset/xtts_v2'),
            language=tts_config_data.get('language', 'en'),
            device=tts_config_data.get('device', 'cpu')
        )
        
        try:
            tts_manager = TTSManager(tts_config)
            console.print("✓ Text-to-speech loaded (Coqui TTS)")
        except Exception as e:
            logger.warning(f"TTS initialization failed: {e}")
            console.print("[yellow]✗ TTS not available (continuing without voice output)[/yellow]")
            tts_manager = None
        
        # Steve factory
        factory = SteveFactory(memory, llm)
        
        # Orchestrator
        orchestrator_config = self.config.get('orchestrator', {})
        max_agents = orchestrator_config.get('max_agents', 10)
        self.orchestrator = Orchestrator(memory, stt, tts_manager, factory, max_agents)
        console.print("✓ Orchestrator initialized")
        
        # Audio input
        audio_config_data = self.config.get('audio', {})
        audio_config = AudioConfig(
            device=audio_config_data.get('input_device'),
            sample_rate=audio_config_data.get('sample_rate', 16000),
            channels=audio_config_data.get('channels', 1),
            chunk_size=audio_config_data.get('chunk_size', 1024),
            vad_enabled=audio_config_data.get('vad_enabled', True),
            vad_threshold=audio_config_data.get('vad_threshold', 0.5)
        )
        self.audio_input = AudioInput(audio_config)
        console.print("✓ Audio input configured")
        
        # Audio output
        self.audio_output = AudioOutput(device=audio_config_data.get('output_device'))
        
        # Streaming transcriber
        stt_config_data = self.config.get('stt', {})
        silence_duration = stt_config_data.get('silence_duration', 1.5)
        
        self.streaming_transcriber = StreamingTranscriber(
            stt=stt,
            buffer_duration=3.0,
            sample_rate=audio_config.sample_rate,
            callback=self._on_transcription,
            silence_duration=silence_duration
        )
        
        console.print("\n[green]✓ All components initialized successfully![/green]\n")
    
    def _on_transcription(self, text: str):
        """Callback for streaming transcription"""
        if not text.strip():
            return
        
        console.print(f"[blue]You:[/blue] {text}")
        
        # Process input
        response = self.orchestrator.process_input(text)
        
        console.print(f"[green]{self.orchestrator.active_agent.persona.name if self.orchestrator.active_agent else 'System'}:[/green] {response}")
        
        # Speak response if TTS available
        if self.orchestrator.tts_manager and self.orchestrator.active_agent:
            try:
                audio = self.orchestrator.tts_manager.synthesize_with_profile(
                    text=response,
                    profile_name=self.orchestrator.active_agent.persona.name
                )
                if audio is not None:
                    self.audio_output.play(audio)
            except Exception as e:
                logger.debug(f"TTS playback failed: {e}")
    
    def load_personas(self, persona_paths: list):
        """Load personas from files"""
        for path in persona_paths:
            try:
                steve = self.orchestrator.steve_factory.create_from_config(path)
                self.orchestrator.add_agent(steve)
                console.print(f"✓ Loaded persona: {steve.persona.name}")
            except Exception as e:
                console.print(f"[red]✗ Failed to load persona {path}: {e}[/red]")
    
    def run_interactive(self):
        """Run in interactive text mode"""
        console.print(Panel(
            "[bold]Interactive Mode[/bold]\n"
            "Type your messages or use voice commands.\n"
            "Type 'quit' to exit.",
            border_style="green"
        ))
        
        self.orchestrator.start()
        
        try:
            while True:
                try:
                    user_input = console.input("\n[blue]You:[/blue] ")
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    
                    if not user_input.strip():
                        continue
                    
                    # Process input
                    response = self.orchestrator.process_input(user_input)
                    
                    agent_name = self.orchestrator.active_agent.persona.name if self.orchestrator.active_agent else "System"
                    console.print(f"[green]{agent_name}:[/green] {response}")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
        
        finally:
            self.orchestrator.stop()
            console.print("\n[yellow]Goodbye![/yellow]")
    
    def run_voice_mode(self):
        """Run in voice interaction mode"""
        console.print(Panel(
            "[bold]Voice Mode[/bold]\n"
            "Speak into your microphone.\n"
            "Press Ctrl+C to stop.",
            border_style="green"
        ))
        
        self.orchestrator.start()
        self.audio_input.start_recording()
        self.streaming_transcriber.start()
        
        try:
            console.print("\n[yellow]🎤 Listening...[/yellow]\n")
            
            while True:
                # Get audio chunk
                chunk = self.audio_input.get_audio_chunk(timeout=0.5)
                if chunk is not None:
                    self.streaming_transcriber.add_audio(chunk)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.streaming_transcriber.stop()
            self.audio_input.stop_recording()
            self.orchestrator.stop()
            console.print("\n[yellow]Goodbye![/yellow]")
    
    def show_status(self):
        """Display system status"""
        status = self.orchestrator.get_status()
        
        table = Table(title="bot-o'clock Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        
        table.add_row("Running", "✓" if status['running'] else "✗")
        table.add_row("Active Agents", str(status['agents']))
        table.add_row("Current Agent", status['active_agent'] or "None")
        table.add_row("Audio Inputs", str(status['audio_inputs']))
        table.add_row("Audio Outputs", str(status['audio_outputs']))
        
        console.print(table)
        
        # List agents
        if status['agents'] > 0:
            agents_table = Table(title="Agents")
            agents_table.add_column("Name", style="cyan")
            agents_table.add_column("Model", style="yellow")
            agents_table.add_column("Active", style="green")
            
            for name, agent in self.orchestrator.agents.items():
                is_active = "✓" if name == status['active_agent'] else ""
                agents_table.add_row(name, agent.persona.model, is_active)
            
            console.print(agents_table)


@click.group()
def cli():
    """bot-o'clock - Local voice-driven multi-agent AI framework"""
    pass


@cli.command()
@click.option('--config', default='config/settings.yaml', help='Configuration file path')
@click.option('--persona', multiple=True, help='Persona file(s) to load')
@click.option('--mode', type=click.Choice(['voice', 'text']), default='text', help='Interaction mode')
@click.option('--log-level', default='INFO', help='Logging level')
def run(config, persona, mode, log_level):
    """Start bot-o'clock"""
    setup_logging(log_level)
    
    # Load configuration
    config_data = load_config(config)
    
    # Initialize app
    app = BotOClock(config_data)
    app.initialize()
    
    # Load personas
    if persona:
        app.load_personas(persona)
    else:
        # Create default agent
        default_persona = config_data.get('orchestrator', {}).get('default_persona')
        if default_persona and os.path.exists(default_persona):
            app.load_personas([default_persona])
        else:
            # Create a basic default agent
            steve = app.orchestrator.create_agent_from_template("Steve", "default")
            console.print("✓ Created default agent: Steve")
    
    # Run
    if mode == 'voice':
        app.run_voice_mode()
    else:
        app.run_interactive()


@cli.command()
@click.option('--config', default='config/settings.yaml', help='Configuration file path')
def status(config):
    """Show system status"""
    setup_logging('WARNING')
    config_data = load_config(config)
    
    app = BotOClock(config_data)
    app.initialize()
    app.show_status()


@cli.command()
def devices():
    """List audio devices"""
    from audio_input import AudioInput
    from tts import AudioOutput
    
    console.print("\n[bold]Input Devices:[/bold]")
    input_devices = AudioInput.list_devices()
    for idx, info in input_devices.items():
        default = " (default)" if idx == AudioInput.get_default_device() else ""
        console.print(f"  [{idx}] {info['name']}{default}")
    
    console.print("\n[bold]Output Devices:[/bold]")
    output_devices = AudioOutput.list_output_devices()
    for idx, info in output_devices.items():
        console.print(f"  [{idx}] {info['name']}")


@cli.command()
@click.argument('name')
@click.option('--template', default='default', help='Template type (default, assistant, creative)')
@click.option('--output', default='personas', help='Output directory')
def create_persona(name, template, output):
    """Create a new persona file"""
    from steve import PersonaConfig
    
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
        traits=template_data['traits']
    )
    
    # Create output directory
    os.makedirs(output, exist_ok=True)
    
    # Save persona
    output_path = os.path.join(output, f"{name.lower()}.yaml")
    persona.to_yaml(output_path)
    
    console.print(f"[green]✓ Created persona file: {output_path}[/green]")


if __name__ == "__main__":
    cli()
