#!/usr/bin/env python3
"""
Example client for testing the AI Website Navigator Backend
"""

import asyncio
import json
import httpx
from typing import List, Dict, Any

# Example DOM elements that might be found on an e-commerce site
SAMPLE_DOM_ELEMENTS = [
    {
        "id": 0,
        "tag": "input",
        "text": "",
        "type": "search",
        "placeholder": "Search products..."
    },
    {
        "id": 1,
        "tag": "button",
        "text": "Search"
    },
    {
        "id": 2,
        "tag": "a",
        "text": "Home"
    },
    {
        "id": 3,
        "tag": "a",
        "text": "Products"
    },
    {
        "id": 4,
        "tag": "a",
        "text": "Cart (0)"
    },
    {
        "id": 5,
        "tag": "button",
        "text": "Add to Cart"
    },
    {
        "id": 6,
        "tag": "div",
        "text": "Leather Wallet - $29.99"
    },
    {
        "id": 7,
        "tag": "button",
        "text": "Buy Now"
    }
]

class AINavigatorClient:
    """Client for testing the AI Navigator API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the backend is healthy"""
        response = await self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get backend statistics"""
        response = await self.session.get(f"{self.base_url}/stats")
        response.raise_for_status()
        return response.json()
    
    async def plan_action(
        self, 
        query: str, 
        dom_elements: List[Dict[str, Any]] = None,
        history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Request next action from AI"""
        
        payload = {
            "query": query,
            "dom_snapshot": dom_elements or SAMPLE_DOM_ELEMENTS,
            "history": history or []
        }
        
        response = await self.session.post(f"{self.base_url}/plan", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def submit_feedback(
        self,
        query: str,
        success: bool,
        actions: List[Dict[str, Any]],
        dom_snapshot: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submit feedback about an interaction"""
        
        payload = {
            "query": query,
            "success": success,
            "actions": actions,
            "dom_snapshot": dom_snapshot or SAMPLE_DOM_ELEMENTS
        }
        
        response = await self.session.post(f"{self.base_url}/feedback", json=payload)
        response.raise_for_status()
        return response.json()

async def test_basic_functionality():
    """Test basic API functionality"""
    
    async with AINavigatorClient() as client:
        print("🔍 Testing AI Website Navigator Backend")
        print("=" * 50)
        
        # Health check
        try:
            health = await client.health_check()
            print(f"✅ Health Check: {health['status']}")
            print(f"   Environment: {health['environment']}")
            print(f"   AI Model: {health['ai_model']}")
        except Exception as e:
            print(f"❌ Health Check Failed: {e}")
            return
        
        # Get stats
        try:
            stats = await client.get_stats()
            print(f"📊 Stats: Cache size: {stats['cache_size']}, Patterns: {stats['patterns_count']}")
        except Exception as e:
            print(f"⚠️  Stats Error: {e}")
        
        print("\n🤖 Testing AI Decision Making")
        print("-" * 30)
        
        # Test cases
        test_cases = [
            "search for leather wallet",
            "add this item to my cart",
            "go to checkout",
            "navigate to the home page",
            "find products under $50"
        ]
        
        for i, query in enumerate(test_cases, 1):
            try:
                print(f"\n{i}. Query: '{query}'")
                
                result = await client.plan_action(query)
                
                action = result['action']
                element_id = result.get('elementId')
                text = result.get('text')
                reasoning = result.get('reasoning', 'No reasoning provided')
                confidence = result.get('confidence', 'N/A')
                
                print(f"   Action: {action}")
                if element_id is not None:
                    print(f"   Target Element: {element_id}")
                if text:
                    print(f"   Text: '{text}'")
                print(f"   Reasoning: {reasoning}")
                print(f"   Confidence: {confidence}")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")

async def test_multi_step_interaction():
    """Test a complete multi-step interaction"""
    
    async with AINavigatorClient() as client:
        print("\n🔄 Testing Multi-Step Interaction")
        print("=" * 40)
        print("Scenario: Search for 'leather wallet' and add to cart")
        
        query = "search for leather wallet and add it to cart"
        history = []
        
        for step in range(1, 6):  # Max 5 steps
            print(f"\n--- Step {step} ---")
            
            try:
                result = await client.plan_action(query, history=history)
                
                action = result['action']
                print(f"Action: {action}")
                
                if action == "DONE":
                    summary = result.get('summary', 'Task completed')
                    print(f"✅ Completed: {summary}")
                    break
                
                # Simulate adding action to history
                new_action = {
                    "action": action,
                    "elementId": result.get('elementId'),
                    "text": result.get('text')
                }
                history.append(new_action)
                
                element_id = result.get('elementId')
                text = result.get('text')
                reasoning = result.get('reasoning', 'No reasoning')
                
                if element_id is not None:
                    print(f"Target Element: {element_id}")
                if text:
                    print(f"Text to Type: '{text}'")
                print(f"Reasoning: {reasoning}")
                
            except Exception as e:
                print(f"❌ Error in step {step}: {e}")
                break
        
        # Submit feedback
        if history:
            try:
                feedback_result = await client.submit_feedback(
                    query=query,
                    success=True,
                    actions=history
                )
                print(f"\n📝 Feedback submitted: {feedback_result['status']}")
            except Exception as e:
                print(f"⚠️  Feedback error: {e}")

async def main():
    """Main test function"""
    
    print("🚀 AI Website Navigator Backend Test Client")
    print("=" * 60)
    
    try:
        # Test basic functionality
        await test_basic_functionality()
        
        # Test multi-step interaction
        await test_multi_step_interaction()
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
