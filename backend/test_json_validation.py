#!/usr/bin/env python3
"""
Quick test script to verify JSON validation is working correctly
"""

import asyncio
import json
from models import LLMActionPlanSchema, LLMIntentAnalysisSchema
from json_validation import LLMJSONValidator, JSONValidationError

async def test_json_validation():
    """Test the JSON validation system with valid and invalid inputs"""
    
    print("🧪 Testing JSON Validation System")
    print("=" * 50)
    
    # Test valid intent analysis JSON
    valid_intent_json = """
    {
        "primary_intent": "SEARCH",
        "entities": ["leather wallet"],
        "required_steps": ["click search input", "type search term", "click search button"],
        "confidence": 0.9
    }
    """
    
    try:
        result = LLMIntentAnalysisSchema.model_validate_json(valid_intent_json)
        print("✅ Valid intent analysis JSON parsed successfully")
        print(f"   Intent: {result.primary_intent}, Confidence: {result.confidence}")
    except Exception as e:
        print(f"❌ Valid intent analysis JSON failed: {e}")
    
    # Test invalid intent analysis JSON (missing required field)
    invalid_intent_json = """
    {
        "primary_intent": "SEARCH",
        "entities": ["leather wallet"],
        "confidence": 0.9
    }
    """
    
    try:
        result = LLMIntentAnalysisSchema.model_validate_json(invalid_intent_json)
        print("❌ Invalid intent analysis JSON should have failed but didn't")
    except Exception as e:
        print("✅ Invalid intent analysis JSON correctly rejected")
        print(f"   Error: {e}")
    
    # Test valid action plan JSON
    valid_action_json = """
    {
        "current_step": 1,
        "total_steps": 3,
        "next_action": {
            "action": "CLICK",
            "elementId": 5,
            "text": null,
            "summary": null
        },
        "reasoning": "User wants to search, so click on search input field",
        "alternative_actions": []
    }
    """
    
    try:
        result = LLMActionPlanSchema.model_validate_json(valid_action_json)
        print("✅ Valid action plan JSON parsed successfully")
        print(f"   Action: {result.next_action.action}, Element: {result.next_action.elementId}")
    except Exception as e:
        print(f"❌ Valid action plan JSON failed: {e}")
    
    # Test invalid action plan JSON (invalid step numbers)
    invalid_action_json = """
    {
        "current_step": 0,
        "total_steps": -1,
        "next_action": {
            "action": "CLICK",
            "elementId": 5,
            "text": null,
            "summary": null
        },
        "reasoning": "",
        "alternative_actions": []
    }
    """
    
    try:
        result = LLMActionPlanSchema.model_validate_json(invalid_action_json)
        print("❌ Invalid action plan JSON should have failed but didn't")
    except Exception as e:
        print("✅ Invalid action plan JSON correctly rejected")
        print(f"   Error: {e}")
    
    print("\n🎉 JSON validation tests completed!")

if __name__ == "__main__":
    asyncio.run(test_json_validation())
