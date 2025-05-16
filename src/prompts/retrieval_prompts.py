from typing import Optional, List

class RetrievalPrompts:
    @staticmethod
    def get_focused_search_prompt(
        query: str,
        doc_types: Optional[List[str]] = None,
        include_relationships: bool = False
    ) -> str:
        """Generate a focused search prompt that encourages concise, specific answers."""
        type_filter = f" within {', '.join(doc_types)}" if doc_types else ""
        
        # Check for basic greetings and questions
        basic_greeting_patterns = ["hi", "hello", "hey", "greetings", "how are you", "what's up", "howdy"]
        if any(greeting in query.lower() for greeting in basic_greeting_patterns):
            return f"""
            This appears to be a basic greeting or introduction:

            {query}

            Instructions:
            1. Do NOT use search_nodes or any knowledge retrieval tools
            2. Respond directly to the greeting with a friendly introduction
            3. Introduce yourself as a "Noob Agent" in your response
            4. Offer to help without using external data

            Response Format:
            Answer: [A friendly greeting followed by a brief introduction as a Noob Agent]

            Examples of GOOD responses:
            Query: "Hi there"
            Answer: Hello! I'm your Noob Agent. How can I help you today?

            Query: "Hey, how are you?"
            Answer: I'm doing well, thanks for asking! I'm the Noob Agent here to assist you with any questions or tasks you have.

            CRITICAL RULES:
            1. NEVER use knowledge retrieval tools for basic greetings
            2. Keep the response friendly and concise
            3. ALWAYS introduce yourself as a "Noob Agent"
            4. Offer to help without making assumptions about what the user needs
            """
        
        return f"""
        Find specific information{type_filter} about:

        {query}

        Instructions:
        1. Use search_nodes to find ONLY the specific information that answers the query
        2. If the query is about conversation history, ONLY use the most recent relevant interaction
        3. For all other queries, use ONLY the most recent relevant information from the knowledge graph
        4. Return ONLY the exact information requested - nothing more
        5. Format as a single, clear sentence
        6. Include the exact source from search_nodes

        Response Rules:
        - For location queries: Return ONLY current location
        - For date queries: Return ONLY the specific date
        - For status queries: Return ONLY current status
        - For numerical queries: Return ONLY the number/value
        - For name queries: Return ONLY the name
        - For conversation history: Return ONLY the exact last query/response
        - For personal info: Return ONLY the specific requested detail

        Format your response EXACTLY as:
        Answer: [Single sentence with ONLY the requested information]
        Source: [Exact source from search_nodes]

        Examples of GOOD responses:
        Query: "What is Alex's role?"
        Answer: Alex Johnson is a Software Engineer at TechCorp.
        Source: [Employee_Profile | 2024-02-15 | Current Role]

        Query: "What was my last question?"
        Answer: Your last question was about API integration.
        Source: [Conversation_History | 2024-02-15 | Recent Query]

        Examples of BAD responses (DO NOT DO THESE):
        ❌ "Alex Johnson is a Software Engineer with 5 years of experience..."
        ❌ "Your last question was about API integration, and we discussed..."
        ❌ "Based on the conversation history, you asked about..."

        CRITICAL RULES:
        1. NEVER include additional context or information
        2. NEVER mention historical data unless specifically asked
        3. NEVER add explanations or qualifiers
        4. NEVER combine information from multiple sources
        5. NEVER make assumptions about the data
        6. NEVER include personal opinions or interpretations
        7. For conversation history, ONLY return the exact last query
        8. Use ONLY the most recent relevant source
        9. If information is not found, respond with "No information found for this query"
        """

    @staticmethod
    def get_detailed_search_prompt(
        query: str,
        doc_types: Optional[List[str]] = None,
        include_relationships: bool = True
    ) -> str:
        """Generate a detailed search prompt for comprehensive information requests."""
        type_filter = f" within {', '.join(doc_types)}" if doc_types else ""
        
        return f"""
        Search for comprehensive information{type_filter} about:
        
        {query}
        
        Instructions:
        1. Use search_nodes to find all relevant information
        2. Use search_facts to find relationships between pieces of information
        3. Extract key insights and details
        4. For each piece of information and relationship:
           - Include the exact source from the tool results
           - Specify which tool provided the information
        
        Format your response as:
        Answer: A detailed, well-structured response
        
        Sources:
        From search_nodes:
        - [Include exact source details from the tool]
        
        From search_facts:
        - [Include exact relationship and source details from the tool]
        
        Important:
        - Only use information and sources provided by the tools
        - Do not infer or assume source details
        - Clearly indicate which tool provided each piece of information
        """

    @staticmethod
    def get_timeline_search_prompt(
        query: str,
        doc_types: Optional[List[str]] = None
    ) -> str:
        """Generate a timeline-focused search prompt for chronological information."""
        type_filter = f" within {', '.join(doc_types)}" if doc_types else ""
        
        return f"""
        Search for chronological information{type_filter} about:
        
        {query}
        
        Instructions:
        1. Use search_nodes to find time-based information
        2. Extract and sort events chronologically
        3. For each event:
           - Include the exact source from search_nodes
           - Include any temporal relationships from search_facts
        
        Format your response as:
        Timeline:
        [Date/Time] Event/Change/Update
        Source: [Exact source details from the tool result]
        
        Important:
        - Sort from earliest to latest
        - Only include dated information
        - Use exact source details from the tools
        - Do not infer or assume source information
        """ 