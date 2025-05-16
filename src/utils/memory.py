from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from src.config.settings import CONVERSATION_MEMORY_SIZE

class ConversationMemoryManager:
    """Manages conversation memory with a fixed window of recent interactions."""
    
    def __init__(self, k: int = CONVERSATION_MEMORY_SIZE):
        """Initialize the memory manager.
        
        Args:
            k: Number of conversations to keep in memory (defaults to CONVERSATION_MEMORY_SIZE from settings)
        """
        self.k = k
        self.chat_history: BaseChatMessageHistory = ChatMessageHistory()
    
    def add_interaction(self, human_message: str, ai_message: str) -> None:
        """Add a human-AI interaction to memory.
        
        Args:
            human_message: The user's message
            ai_message: The AI's response
        """
        self.chat_history.add_message(HumanMessage(content=human_message))
        self.chat_history.add_message(AIMessage(content=ai_message))
        
        # Keep only the last k interactions (2 messages per interaction)
        if len(self.chat_history.messages) > self.k * 2:
            self.chat_history.messages = self.chat_history.messages[-self.k * 2:]
    
    def get_chat_history(self) -> List[BaseMessage]:
        """Retrieve the chat history as a list of messages.
        
        Returns:
            List of chat messages
        """
        return self.chat_history.messages
    
    def get_formatted_history(self) -> str:
        """Get the chat history formatted as a string.
        
        Returns:
            Formatted chat history string
        """
        messages = self.get_chat_history()
        formatted_history = []
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_history.append(f"Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted_history.append(f"Assistant: {msg.content}")
                
        return "\n".join(formatted_history)
    
    def clear(self) -> None:
        """Clear the conversation memory."""
        self.chat_history.clear() 