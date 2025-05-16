import mimetypes
from typing import Optional

class IngestionPrompts:
    @staticmethod
    def get_document_processing_prompt(
        file_path: str,
        mime_type: Optional[str] = None,
        extract_metadata: bool = True
    ) -> str:
        """Generate a document processing prompt based on file type."""
        file_type = mime_type or mimetypes.guess_type(file_path)[0] or "unknown"
        metadata_instruction = (
            "\n4. Extract and store document metadata (author, date, version, etc.)"
            if extract_metadata else ""
        )
        
        base_prompt = f"""
        Process this document efficiently and store key information:
        
        File: {file_path}
        Type: {file_type}
        
        Instructions:
        1. Use appropriate MarkItDown tools for the file type
        2. Extract ONLY relevant information and insights
        3. Store processed content using add_episode{metadata_instruction}
        
        Focus on:
        - Key facts and data points
        - Important statements
        - Numerical values
        - Dates and timestamps
        - Names and entities
        - Locations
        - Status information
        
        DO NOT store:
        - Formatting details
        - Redundant information
        - Generic content
        - Boilerplate text
        """
        
        # Add file-type specific instructions
        if "pdf" in file_type:
            base_prompt += """
            PDF-specific:
            - Extract text from all pages
            - Process tables and structured data
            - Handle embedded images with OCR if needed
            """
        elif "image" in file_type:
            base_prompt += """
            Image-specific:
            - Use OCR to extract text
            - Process any visible data or charts
            - Extract text from diagrams
            """
        elif "spreadsheet" in file_type or "excel" in file_type:
            base_prompt += """
            Spreadsheet-specific:
            - Process all relevant sheets
            - Extract tabular data
            - Preserve data relationships
            - Handle formulas and calculated values
            """
            
        return base_prompt

    @staticmethod
    def get_relationship_prompt(doc_id: str) -> str:
        """Generate a prompt for establishing document relationships."""
        return f"""
        Analyze and establish relationships for document {doc_id}:
        
        Instructions:
        1. Use search_facts to find related documents
        2. Identify key relationships:
           - Parent/child relationships
           - Referenced documents
           - Similar topics or content
           - Temporal relationships
           - Dependency relationships
        
        3. Create relationship links:
           - Use appropriate relationship types
           - Include relationship metadata
           - Ensure bidirectional relationships where appropriate
        
        4. Validate relationships:
           - Check for circular references
           - Verify relationship strength
           - Confirm relationship validity
        """

    @staticmethod
    def get_metadata_extraction_prompt() -> str:
        """Generate a prompt for metadata extraction."""
        return """
        Extract and structure document metadata:
        
        Focus on:
        1. Document Properties
           - Title
           - Author(s)
           - Creation date
           - Last modified date
           - Version information
           
        2. Content Metadata
           - Document type
           - Language
           - Topic categories
           - Keywords/tags
           
        3. Technical Metadata
           - File format
           - Size
           - Encoding
           - Processing status
        
        Format metadata consistently and include only available information.
        DO NOT make assumptions about missing metadata.
        """ 