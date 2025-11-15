"""
Memory and Storage Layer for bot-o'clock
Handles conversation history and agent memory using SQLite
"""

import sqlite3
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a single message in conversation history"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: str
    agent_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        if self.metadata:
            data['metadata'] = json.dumps(self.metadata)
        return data
    
    @staticmethod
    def from_dict(data: dict) -> 'Message':
        """Create from dictionary"""
        if 'metadata' in data and isinstance(data['metadata'], str):
            data['metadata'] = json.loads(data['metadata'])
        return Message(**data)


@dataclass
class Conversation:
    """Represents a conversation session"""
    id: int
    agent_name: str
    started_at: str
    ended_at: Optional[str] = None
    title: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


class MemoryStore:
    """
    SQLite-based memory store for agent conversations
    Thread-safe implementation for concurrent access
    """
    
    def __init__(self, db_path: str = "data/memories.db"):
        self.db_path = db_path
        self._local = threading.local()
        
        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        logger.info(f"MemoryStore initialized: {db_path}")
    
    @property
    def conn(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                title TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agent_name TEXT,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        
        # Agent state table (for persistent agent data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_state (
                agent_name TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation 
            ON messages(conversation_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_agent 
            ON messages(agent_name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_agent 
            ON conversations(agent_name)
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database schema initialized")
    
    def create_conversation(self, agent_name: str, title: Optional[str] = None) -> int:
        """
        Create a new conversation
        
        Args:
            agent_name: Name of the agent
            title: Optional conversation title
            
        Returns:
            Conversation ID
        """
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO conversations (agent_name, started_at, title)
            VALUES (?, ?, ?)
        """, (agent_name, timestamp, title))
        
        self.conn.commit()
        conversation_id = cursor.lastrowid
        logger.info(f"Created conversation {conversation_id} for agent {agent_name}")
        return conversation_id
    
    def end_conversation(self, conversation_id: int):
        """Mark a conversation as ended"""
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        
        cursor.execute("""
            UPDATE conversations 
            SET ended_at = ? 
            WHERE id = ?
        """, (timestamp, conversation_id))
        
        self.conn.commit()
    
    def add_message(self, conversation_id: int, message: Message):
        """
        Add a message to a conversation
        
        Args:
            conversation_id: ID of the conversation
            message: Message to add
        """
        cursor = self.conn.cursor()
        
        metadata_json = json.dumps(message.metadata) if message.metadata else None
        
        cursor.execute("""
            INSERT INTO messages 
            (conversation_id, role, content, agent_name, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            conversation_id,
            message.role,
            message.content,
            message.agent_name,
            message.timestamp,
            metadata_json
        ))
        
        self.conn.commit()
    
    def get_messages(
        self,
        conversation_id: int,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Message]:
        """
        Get messages from a conversation
        
        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of messages
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT role, content, agent_name, timestamp, metadata
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        """
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor.execute(query, (conversation_id,))
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            metadata = json.loads(row['metadata']) if row['metadata'] else None
            messages.append(Message(
                role=row['role'],
                content=row['content'],
                agent_name=row['agent_name'],
                timestamp=row['timestamp'],
                metadata=metadata
            ))
        
        return messages
    
    def get_recent_messages(
        self,
        agent_name: str,
        limit: int = 20
    ) -> List[Message]:
        """
        Get recent messages for an agent across all conversations
        
        Args:
            agent_name: Name of the agent
            limit: Maximum number of messages
            
        Returns:
            List of recent messages
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT role, content, agent_name, timestamp, metadata
            FROM messages
            WHERE agent_name = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (agent_name, limit))
        
        rows = cursor.fetchall()
        messages = []
        
        for row in rows:
            metadata = json.loads(row['metadata']) if row['metadata'] else None
            messages.append(Message(
                role=row['role'],
                content=row['content'],
                agent_name=row['agent_name'],
                timestamp=row['timestamp'],
                metadata=metadata
            ))
        
        return list(reversed(messages))  # Return in chronological order
    
    def get_conversations(
        self,
        agent_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Conversation]:
        """
        Get conversations, optionally filtered by agent
        
        Args:
            agent_name: Filter by agent name (optional)
            limit: Maximum number of conversations
            
        Returns:
            List of conversations
        """
        cursor = self.conn.cursor()
        
        if agent_name:
            cursor.execute("""
                SELECT id, agent_name, started_at, ended_at, title
                FROM conversations
                WHERE agent_name = ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (agent_name, limit))
        else:
            cursor.execute("""
                SELECT id, agent_name, started_at, ended_at, title
                FROM conversations
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conversations = []
        
        for row in rows:
            conversations.append(Conversation(
                id=row['id'],
                agent_name=row['agent_name'],
                started_at=row['started_at'],
                ended_at=row['ended_at'],
                title=row['title']
            ))
        
        return conversations
    
    def save_agent_state(self, agent_name: str, state_data: dict):
        """
        Save agent state data
        
        Args:
            agent_name: Name of the agent
            state_data: State data to save
        """
        cursor = self.conn.cursor()
        timestamp = datetime.utcnow().isoformat()
        state_json = json.dumps(state_data)
        
        cursor.execute("""
            INSERT OR REPLACE INTO agent_state (agent_name, state_data, updated_at)
            VALUES (?, ?, ?)
        """, (agent_name, state_json, timestamp))
        
        self.conn.commit()
    
    def load_agent_state(self, agent_name: str) -> Optional[dict]:
        """
        Load agent state data
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            State data or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT state_data FROM agent_state WHERE agent_name = ?
        """, (agent_name,))
        
        row = cursor.fetchone()
        if row:
            return json.loads(row['state_data'])
        return None
    
    def clear_agent_data(self, agent_name: str):
        """Delete all data for an agent"""
        cursor = self.conn.cursor()
        
        # Get conversation IDs
        cursor.execute("""
            SELECT id FROM conversations WHERE agent_name = ?
        """, (agent_name,))
        conversation_ids = [row['id'] for row in cursor.fetchall()]
        
        # Delete messages
        if conversation_ids:
            placeholders = ','.join(['?'] * len(conversation_ids))
            cursor.execute(f"""
                DELETE FROM messages WHERE conversation_id IN ({placeholders})
            """, conversation_ids)
        
        # Delete conversations
        cursor.execute("""
            DELETE FROM conversations WHERE agent_name = ?
        """, (agent_name,))
        
        # Delete agent state
        cursor.execute("""
            DELETE FROM agent_state WHERE agent_name = ?
        """, (agent_name,))
        
        self.conn.commit()
        logger.info(f"Cleared all data for agent: {agent_name}")
    
    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()


if __name__ == "__main__":
    # Test memory store
    logging.basicConfig(level=logging.INFO)
    
    print("Testing MemoryStore...")
    
    # Create test database
    store = MemoryStore("data/test_memories.db")
    
    # Create conversation
    conv_id = store.create_conversation("TestSteve", "Test Conversation")
    print(f"Created conversation: {conv_id}")
    
    # Add messages
    store.add_message(conv_id, Message(
        role="user",
        content="Hello, Steve!",
        timestamp=datetime.utcnow().isoformat(),
        agent_name="TestSteve"
    ))
    
    store.add_message(conv_id, Message(
        role="assistant",
        content="Hello! How can I help you?",
        timestamp=datetime.utcnow().isoformat(),
        agent_name="TestSteve"
    ))
    
    # Retrieve messages
    messages = store.get_messages(conv_id)
    print(f"\nRetrieved {len(messages)} messages:")
    for msg in messages:
        print(f"  [{msg.role}] {msg.content}")
    
    # End conversation
    store.end_conversation(conv_id)
    
    print("\nMemoryStore test completed!")
