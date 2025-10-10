"""
Conversation Manager - Redis-based conversation history storage
"""

import json
import redis
import os
import logging
import sys
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler('finops-conversation-manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversation history using Redis"""

    def __init__(self):
        """Initialize Redis connection"""
        logger.info("Initializing ConversationManager")
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', 6379))
        self.redis_password = os.getenv('REDIS_PASSWORD', None)
        self.redis_db = int(os.getenv('REDIS_DB', 0))

        logger.debug(f"Redis config: host={self.redis_host}, port={self.redis_port}, db={self.redis_db}")

        try:
            logger.debug("Connecting to Redis...")
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                db=self.redis_db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"✓ Redis connected: {self.redis_host}:{self.redis_port}")
            print(f"✓ Redis connected: {self.redis_host}:{self.redis_port}")
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection failed: {e}")
            print(f"⚠️  Redis connection failed: {e}")
            print("  Using in-memory storage (conversations won't persist)")
            self.redis_client = None
            self._memory_store = {}  # Fallback to in-memory storage

    def _get_conversation_key(self, conversation_id: str) -> str:
        """Get Redis key for a conversation"""
        return f"finops:conversation:{conversation_id}"

    def _get_conversation_list_key(self) -> str:
        """Get Redis key for conversation list"""
        return "finops:conversations"

    def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for session data"""
        return f"finops:session:{session_id}"

    def create_conversation(self, session_id: str = None, title: str = None) -> str:
        """Create a new conversation and return its ID"""
        logger.info("=" * 80)
        logger.info("Creating new conversation")
        logger.debug(f"Session ID: {session_id}, Title: {title}")

        conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        logger.info(f"Generated conversation ID: {conversation_id}")

        conversation = {
            'id': conversation_id,
            'session_id': session_id or 'default',
            'title': title or 'New Conversation',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'messages': [],
            'metadata': {}
        }

        if self.redis_client:
            logger.debug("Storing conversation in Redis")
            # Store conversation
            self.redis_client.set(
                self._get_conversation_key(conversation_id),
                json.dumps(conversation),
                ex=7 * 24 * 3600  # Expire after 7 days
            )

            # Add to conversation list (sorted set by timestamp)
            timestamp = datetime.now(timezone.utc).timestamp()
            self.redis_client.zadd(
                self._get_conversation_list_key(),
                {conversation_id: timestamp}
            )
            logger.info(f"Conversation {conversation_id} stored in Redis")
        else:
            logger.debug("Storing conversation in memory")
            # Fallback to in-memory
            self._memory_store[conversation_id] = conversation
            logger.info(f"Conversation {conversation_id} stored in memory")

        return conversation_id

    def add_message(self, conversation_id: str, role: str, content: str,
                    metadata: Dict[str, Any] = None) -> bool:
        """Add a message to a conversation"""
        logger.debug(f"Adding message to conversation {conversation_id}")
        logger.debug(f"Role: {role}, Content length: {len(content)}")

        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            return False

        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata or {}
        }
        logger.debug(f"Created message object with timestamp {message['timestamp']}")

        conversation['messages'].append(message)
        conversation['updated_at'] = datetime.now(timezone.utc).isoformat()

        # Update title from first user message if not set
        if role == 'user' and conversation['title'] == 'New Conversation':
            conversation['title'] = content[:50] + ('...' if len(content) > 50 else '')

        return self._save_conversation(conversation)

    def add_tool_execution(self, conversation_id: str, tool_name: str,
                          tool_input: Dict[str, Any], tool_output: Any) -> bool:
        """Add a tool execution to the conversation"""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False

        # For chart visualizations, store the full output (it's small JSON)
        # For other tools, limit output size to prevent bloat
        if tool_name == 'create_visualization':
            # Store full chart data as JSON for proper reconstruction
            if isinstance(tool_output, dict):
                output_data = tool_output
            else:
                output_data = str(tool_output)
        else:
            # Limit other tool outputs to 1000 chars
            output_data = str(tool_output)[:1000]

        tool_message = {
            'role': 'tool',
            'tool_name': tool_name,
            'tool_input': tool_input,
            'tool_output': output_data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }

        conversation['messages'].append(tool_message)
        conversation['updated_at'] = datetime.now(timezone.utc).isoformat()

        return self._save_conversation(conversation)

    def _save_conversation(self, conversation: Dict[str, Any]) -> bool:
        """Save conversation to Redis"""
        if self.redis_client:
            try:
                self.redis_client.set(
                    self._get_conversation_key(conversation['id']),
                    json.dumps(conversation),
                    ex=7 * 24 * 3600  # Expire after 7 days
                )
                return True
            except Exception as e:
                print(f"⚠️  Failed to save conversation: {e}")
                return False
        else:
            # Fallback to in-memory
            self._memory_store[conversation['id']] = conversation
            return True

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a conversation by ID"""
        if self.redis_client:
            try:
                data = self.redis_client.get(self._get_conversation_key(conversation_id))
                if data:
                    return json.loads(data)
            except Exception as e:
                print(f"⚠️  Failed to get conversation: {e}")
                return None
        else:
            # Fallback to in-memory
            return self._memory_store.get(conversation_id)

        return None

    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages from a conversation"""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            return conversation.get('messages', [])
        return []

    def list_conversations(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List recent conversations"""
        conversations = []

        if self.redis_client:
            try:
                # Get conversation IDs sorted by timestamp (newest first)
                conversation_ids = self.redis_client.zrevrange(
                    self._get_conversation_list_key(),
                    offset,
                    offset + limit - 1
                )

                for conv_id in conversation_ids:
                    conversation = self.get_conversation(conv_id)
                    if conversation:
                        # Return summary only (without full messages)
                        conversations.append({
                            'id': conversation['id'],
                            'session_id': conversation.get('session_id'),
                            'title': conversation.get('title'),
                            'created_at': conversation.get('created_at'),
                            'updated_at': conversation.get('updated_at'),
                            'message_count': len(conversation.get('messages', []))
                        })
            except Exception as e:
                print(f"⚠️  Failed to list conversations: {e}")
        else:
            # Fallback to in-memory
            for conv_id, conversation in self._memory_store.items():
                conversations.append({
                    'id': conversation['id'],
                    'session_id': conversation.get('session_id'),
                    'title': conversation.get('title'),
                    'created_at': conversation.get('created_at'),
                    'updated_at': conversation.get('updated_at'),
                    'message_count': len(conversation.get('messages', []))
                })
            # Sort by updated_at
            conversations.sort(key=lambda x: x['updated_at'], reverse=True)
            conversations = conversations[offset:offset + limit]

        return conversations

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        if self.redis_client:
            try:
                self.redis_client.delete(self._get_conversation_key(conversation_id))
                self.redis_client.zrem(self._get_conversation_list_key(), conversation_id)
                return True
            except Exception as e:
                print(f"⚠️  Failed to delete conversation: {e}")
                return False
        else:
            # Fallback to in-memory
            if conversation_id in self._memory_store:
                del self._memory_store[conversation_id]
                return True

        return False

    def clear_old_conversations(self, days: int = 7) -> int:
        """Clear conversations older than specified days"""
        if not self.redis_client:
            return 0

        try:
            cutoff_timestamp = (datetime.now(timezone.utc).timestamp() - (days * 24 * 3600))

            # Get old conversation IDs
            old_ids = self.redis_client.zrangebyscore(
                self._get_conversation_list_key(),
                0,
                cutoff_timestamp
            )

            # Delete them
            for conv_id in old_ids:
                self.redis_client.delete(self._get_conversation_key(conv_id))
                self.redis_client.zrem(self._get_conversation_list_key(), conv_id)

            return len(old_ids)
        except Exception as e:
            print(f"⚠️  Failed to clear old conversations: {e}")
            return 0

    def get_session_conversation(self, session_id: str) -> Optional[str]:
        """Get the current conversation ID for a session"""
        if self.redis_client:
            try:
                return self.redis_client.get(self._get_session_key(session_id))
            except Exception as e:
                print(f"⚠️  Failed to get session conversation: {e}")
        return None

    def set_session_conversation(self, session_id: str, conversation_id: str) -> bool:
        """Set the current conversation ID for a session"""
        if self.redis_client:
            try:
                self.redis_client.set(
                    self._get_session_key(session_id),
                    conversation_id,
                    ex=24 * 3600  # Expire after 24 hours
                )
                return True
            except Exception as e:
                print(f"⚠️  Failed to set session conversation: {e}")
        return False

    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()


# Global conversation manager instance
conversation_manager = ConversationManager()
