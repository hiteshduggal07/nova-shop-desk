"""
JSON validation utilities for LLM responses with automatic retry logic
"""

import json
import logging
from typing import TypeVar, Type, Optional, Dict, Any, Callable, Awaitable
from pydantic import BaseModel, ValidationError
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class JSONValidationError(Exception):
    """Custom exception for JSON validation failures"""
    pass

class LLMJSONValidator:
    """Handles strict JSON validation with automatic retry logic for LLM responses"""
    
    def __init__(self, client: AsyncOpenAI, model: str, max_retries: int = 3):
        self.client = client
        self.model = model
        self.max_retries = max_retries
    
    async def validate_and_retry(
        self,
        response_content: str,
        schema_class: Type[T],
        messages: list,
        temperature: float = 0.1,
        max_tokens: int = 800,
        operation_name: str = "LLM operation"
    ) -> T:
        """
        Validate LLM response against schema with automatic retry on validation failure
        
        Args:
            response_content: Raw response from LLM
            schema_class: Pydantic model class to validate against
            messages: Original messages sent to LLM for retry
            temperature: Temperature for retry requests
            max_tokens: Max tokens for retry requests
            operation_name: Name of operation for logging
        
        Returns:
            Validated Pydantic model instance
            
        Raises:
            JSONValidationError: If validation fails after all retries
        """
        
        # Try to validate the original response
        try:
            parsed_json = self._extract_and_parse_json(response_content)
            validated_response = schema_class(**parsed_json)
            logger.debug(f"{operation_name}: JSON validation successful on first attempt")
            return validated_response
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            logger.warning(f"{operation_name}: Initial validation failed: {e}")
            
            # Retry with stricter prompts
            for attempt in range(1, self.max_retries + 1):
                logger.info(f"{operation_name}: Retry attempt {attempt}/{self.max_retries}")
                
                try:
                    # Create stricter prompt for retry
                    retry_messages = self._create_stricter_prompt(messages, schema_class, attempt)
                    
                    # Make retry request
                    retry_response = await self.client.chat.completions.create(
                        model=self.model,
                        messages=retry_messages,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    retry_content = retry_response.choices[0].message.content
                    logger.debug(f"{operation_name}: Retry {attempt} raw response: {retry_content}")
                    
                    # Try to validate retry response
                    parsed_json = self._extract_and_parse_json(retry_content)
                    validated_response = schema_class(**parsed_json)
                    
                    logger.info(f"{operation_name}: JSON validation successful on retry {attempt}")
                    return validated_response
                    
                except (json.JSONDecodeError, ValidationError, ValueError) as e:
                    logger.warning(f"{operation_name}: Retry {attempt} failed: {e}")
                    if attempt == self.max_retries:
                        # Final attempt failed
                        logger.error(f"{operation_name}: All retries exhausted")
                        raise JSONValidationError(
                            f"Failed to get valid JSON after {self.max_retries} retries. "
                            f"Last error: {e}. Last response: {retry_content if 'retry_content' in locals() else response_content}"
                        )
                    continue
    
    def _extract_and_parse_json(self, content: str) -> Dict[str, Any]:
        """Extract and parse JSON from LLM response content"""
        if not content or content.strip() == "":
            raise ValueError("Empty response from LLM")
        
        # Clean up the content
        content = content.strip()
        
        # Remove markdown formatting if present
        if content.startswith("```json"):
            content = content.replace("```json", "").replace("```", "").strip()
        elif content.startswith("```"):
            content = content.replace("```", "").strip()
        
        # Parse JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # Try to find JSON in the content if it's embedded in text
            json_start = content.find('{')
            json_end = content.rfind('}')
            
            if json_start != -1 and json_end != -1 and json_end > json_start:
                json_content = content[json_start:json_end + 1]
                return json.loads(json_content)
            else:
                raise e
    
    def _create_stricter_prompt(
        self, 
        original_messages: list, 
        schema_class: Type[BaseModel], 
        attempt: int
    ) -> list:
        """Create a stricter prompt for retry attempts"""
        
        # Get schema information
        schema_json = schema_class.model_json_schema()
        example = self._generate_example_json(schema_class)
        
        # Create progressively stricter system prompts
        strict_instructions = [
            # Attempt 1: Basic strict instructions
            f"""CRITICAL: You MUST return ONLY valid JSON that matches this exact schema.
            
            Schema: {json.dumps(schema_json, indent=2)}
            
            Example: {example}
            
            RULES:
            1. Return ONLY the JSON object, no other text
            2. Use double quotes for all strings
            3. Follow the exact field names and types
            4. Do not add any explanations or markdown formatting""",
            
            # Attempt 2: More aggressive
            f"""URGENT: Previous response was invalid JSON. You MUST fix this.
            
            REQUIRED SCHEMA: {json.dumps(schema_json, indent=2)}
            
            EXACT EXAMPLE FORMAT: {example}
            
            STRICT REQUIREMENTS:
            - Start response with {{ and end with }}
            - Use exact field names from schema
            - No markdown, no explanations, no extra text
            - Valid JSON syntax only""",
            
            # Attempt 3: Final attempt with minimal viable response
            f"""FINAL ATTEMPT: Return this EXACT format with your values:
            
            {example}
            
            Replace values but keep EXACT structure. NO other text allowed."""
        ]
        
        # Use the appropriate strictness level
        strict_prompt = strict_instructions[min(attempt - 1, len(strict_instructions) - 1)]
        
        # Modify the system message
        modified_messages = original_messages.copy()
        if modified_messages and modified_messages[0]["role"] == "system":
            modified_messages[0] = {
                "role": "system",
                "content": strict_prompt
            }
        else:
            modified_messages.insert(0, {
                "role": "system", 
                "content": strict_prompt
            })
        
        return modified_messages
    
    def _generate_example_json(self, schema_class: Type[BaseModel]) -> str:
        """Generate a valid example JSON for the schema"""
        try:
            # Create an instance with minimal valid data
            if schema_class.__name__ == "LLMActionPlanSchema":
                example = {
                    "current_step": 1,
                    "total_steps": 1,
                    "next_action": {
                        "action": "DONE",
                        "elementId": None,
                        "text": None,
                        "summary": "Task completed"
                    },
                    "reasoning": "Example reasoning",
                    "alternative_actions": []
                }
            elif schema_class.__name__ == "LLMIntentAnalysisSchema":
                example = {
                    "primary_intent": "NAVIGATE",
                    "entities": [],
                    "required_steps": ["Complete user request"],
                    "confidence": 0.8
                }
            else:
                # Fallback: try to create empty instance
                example = schema_class().model_dump()
            
            return json.dumps(example, indent=2)
        except Exception:
            return '{"error": "Could not generate example"}'

# Global validator instance (will be initialized in ai_engine.py)
validator: Optional[LLMJSONValidator] = None

def initialize_validator(client: AsyncOpenAI, model: str, max_retries: int = 3):
    """Initialize the global validator instance"""
    global validator
    validator = LLMJSONValidator(client, model, max_retries)

async def validate_llm_response(
    content: str,
    schema_class: Type[T],
    messages: list,
    operation_name: str = "LLM operation"
) -> T:
    """Convenience function to validate LLM responses using the global validator"""
    if validator is None:
        raise RuntimeError("Validator not initialized. Call initialize_validator() first.")
    
    return await validator.validate_and_retry(
        content, schema_class, messages, operation_name=operation_name
    )
