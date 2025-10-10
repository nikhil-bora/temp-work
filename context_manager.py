"""
Custom Context Manager - Store and manage user-uploaded context for conversations
"""

import os
import json
import time
import base64
from pathlib import Path
from typing import List, Dict, Optional

class ContextManager:
    def __init__(self, storage_dir='custom_contexts'):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.contexts_file = self.storage_dir / 'contexts.json'
        self.contexts = self._load_contexts()

    def _load_contexts(self) -> Dict:
        """Load contexts from JSON file"""
        if self.contexts_file.exists():
            with open(self.contexts_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_contexts(self):
        """Save contexts to JSON file"""
        with open(self.contexts_file, 'w') as f:
            json.dump(self.contexts, f, indent=2)

    def add_context(self, name: str, content: str, description: str = "", context_type: str = "text") -> Dict:
        """Add a new custom context (text or image)"""
        context_id = f"ctx_{int(time.time())}_{name.replace(' ', '_')}"

        # Determine file extension based on type
        if context_type == "image":
            # For images, content is base64 encoded
            context_file = self.storage_dir / f"{context_id}.img"
        else:
            context_file = self.storage_dir / f"{context_id}.txt"

        # Save context content to file
        if context_type == "image":
            # Store base64 image data
            with open(context_file, 'w') as f:
                f.write(content)
        else:
            with open(context_file, 'w') as f:
                f.write(content)

        # Store metadata
        self.contexts[context_id] = {
            'id': context_id,
            'name': name,
            'description': description,
            'file': str(context_file),
            'type': context_type,
            'created': time.time(),
            'size': len(content)
        }

        self._save_contexts()
        return self.contexts[context_id]

    def get_context(self, context_id: str) -> Optional[Dict]:
        """Get context metadata"""
        return self.contexts.get(context_id)

    def get_context_content(self, context_id: str) -> Optional[str]:
        """Get context content"""
        context = self.contexts.get(context_id)
        if not context:
            return None

        context_file = Path(context['file'])
        if context_file.exists():
            with open(context_file, 'r') as f:
                return f.read()
        return None

    def list_contexts(self) -> List[Dict]:
        """List all contexts"""
        return sorted(
            self.contexts.values(),
            key=lambda x: x['created'],
            reverse=True
        )

    def delete_context(self, context_id: str) -> bool:
        """Delete a context"""
        context = self.contexts.get(context_id)
        if not context:
            return False

        # Delete file
        context_file = Path(context['file'])
        if context_file.exists():
            context_file.unlink()

        # Remove from metadata
        del self.contexts[context_id]
        self._save_contexts()
        return True

    def update_context(self, context_id: str, name: str = None, description: str = None, content: str = None) -> Optional[Dict]:
        """Update context metadata or content"""
        context = self.contexts.get(context_id)
        if not context:
            return None

        if name:
            context['name'] = name
        if description is not None:
            context['description'] = description

        if content is not None:
            context_file = Path(context['file'])
            with open(context_file, 'w') as f:
                f.write(content)
            context['size'] = len(content)

        self._save_contexts()
        return context

    def get_contexts_for_prompt(self, context_ids: List[str]) -> str:
        """Get formatted context content for inclusion in system prompt (text only)"""
        if not context_ids:
            return ""

        contexts_text = "\n\n# Custom Context\n\n"
        contexts_text += "The user has provided the following custom context for this conversation:\n\n"

        for context_id in context_ids:
            context = self.get_context(context_id)
            if not context:
                continue

            # Only include text contexts in system prompt
            if context.get('type') == 'image':
                contexts_text += f"## {context['name']} (Image)\n"
                if context.get('description'):
                    contexts_text += f"{context['description']}\n\n"
                contexts_text += "Note: The user has provided an image context. See the first user message for the image.\n\n"
                contexts_text += "---\n\n"
                continue

            content = self.get_context_content(context_id)
            if not content:
                continue

            contexts_text += f"## {context['name']}\n"
            if context.get('description'):
                contexts_text += f"{context['description']}\n\n"
            contexts_text += f"{content}\n\n"
            contexts_text += "---\n\n"

        return contexts_text

    def get_image_contexts(self, context_ids: List[str]) -> List[Dict]:
        """Get image contexts formatted for Claude's vision API"""
        image_contexts = []

        for context_id in context_ids:
            context = self.get_context(context_id)
            if not context or context.get('type') != 'image':
                continue

            content = self.get_context_content(context_id)
            if not content:
                continue

            # Parse media type and base64 data
            if ':' in content:
                media_type, base64_data = content.split(':', 1)
            else:
                media_type = 'image/jpeg'
                base64_data = content

            image_contexts.append({
                'type': 'image',
                'source': {
                    'type': 'base64',
                    'media_type': media_type,
                    'data': base64_data
                }
            })

        return image_contexts
