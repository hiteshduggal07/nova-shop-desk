"""
Tests for the AI Decision Engine
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from ai_engine import AIDecisionEngine
from models import (
    DOMElement, Action, ActionType, NavigatorRequest, 
    IntentAnalysis, ActionPlan, WebsiteContext
)


class TestAIDecisionEngine:
    """Test the main AI Decision Engine class"""
    
    def test_ai_engine_initialization(self, mock_openai_client):
        """Test AI engine initialization"""
        engine = AIDecisionEngine()
        
        assert engine is not None
        assert engine.client is not None
        assert engine.model == "gpt-4o-mini"  # From test settings
    
    @pytest.mark.asyncio
    async def test_analyze_intent_success(self, mock_openai_client):
        """Test successful intent analysis"""
        # Mock OpenAI response
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "primary_intent": "SEARCH",
            "entities": ["leather", "wallet"],
            "required_steps": ["click_search_input", "type_search_term", "submit_search"],
            "confidence": 0.9
        })
        
        engine = AIDecisionEngine()
        intent = await engine.analyze_intent("search for leather wallet", [])
        
        assert intent.primary_intent == "SEARCH"
        assert "leather" in intent.entities
        assert "wallet" in intent.entities
        assert len(intent.required_steps) == 3
        assert intent.confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_analyze_intent_with_history(self, mock_openai_client):
        """Test intent analysis with action history"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "primary_intent": "ADD_TO_CART",
            "entities": ["wallet"],
            "required_steps": ["click_add_to_cart"],
            "confidence": 0.95
        })
        
        history = [
            Action(action=ActionType.CLICK, elementId=0),
            Action(action=ActionType.TYPE, elementId=0, text="leather wallet")
        ]
        
        engine = AIDecisionEngine()
        intent = await engine.analyze_intent("add to cart", history)
        
        assert intent.primary_intent == "ADD_TO_CART"
        assert intent.confidence == 0.95
        
        # Verify OpenAI was called with history
        call_args = mock_openai_client.chat.completions.create.call_args
        assert "Previous Actions" in call_args[1]["messages"][1]["content"]
    
    @pytest.mark.asyncio
    async def test_analyze_intent_error_handling(self, mock_openai_client):
        """Test intent analysis error handling"""
        mock_openai_client.chat.completions.create.side_effect = Exception("OpenAI Error")
        
        engine = AIDecisionEngine()
        intent = await engine.analyze_intent("test query", [])
        
        # Should return fallback intent
        assert intent.primary_intent == "NAVIGATE"
        assert intent.confidence == 0.5
    
    @pytest.mark.asyncio
    async def test_analyze_intent_invalid_json_response(self, mock_openai_client):
        """Test intent analysis with invalid JSON response"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = "invalid json"
        
        engine = AIDecisionEngine()
        intent = await engine.analyze_intent("test query", [])
        
        # Should return fallback intent
        assert intent.primary_intent == "NAVIGATE"
        assert intent.confidence == 0.5
    
    @pytest.mark.asyncio
    async def test_plan_next_action_success(self, mock_openai_client, sample_navigator_request):
        """Test successful action planning"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "current_step": 1,
            "total_steps": 3,
            "next_action": {
                "action": "CLICK",
                "elementId": 0
            },
            "reasoning": "Click on search input to start searching",
            "alternative_actions": []
        })
        
        intent = IntentAnalysis(
            primary_intent="SEARCH",
            entities=["leather", "wallet"],
            required_steps=["click_search", "type_query", "submit"],
            confidence=0.9
        )
        
        website_context = WebsiteContext(
            page_type="home",
            available_actions=["search"],
            common_patterns={"search": "Search input available"},
            navigation_structure={"detected": "basic"}
        )
        
        engine = AIDecisionEngine()
        action_plan = await engine.plan_next_action(sample_navigator_request, intent, website_context)
        
        assert action_plan.current_step == 1
        assert action_plan.total_steps == 3
        assert action_plan.next_action.action == ActionType.CLICK
        assert action_plan.next_action.elementId == 0
        assert "search input" in action_plan.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_plan_next_action_type_action(self, mock_openai_client, sample_navigator_request):
        """Test action planning for TYPE action"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "current_step": 2,
            "total_steps": 3,
            "next_action": {
                "action": "TYPE",
                "elementId": 0,
                "text": "leather wallet"
            },
            "reasoning": "Type search term into the input field",
            "alternative_actions": [
                {"action": "CLICK", "elementId": 1}
            ]
        })
        
        intent = IntentAnalysis(
            primary_intent="SEARCH",
            entities=["leather", "wallet"],
            required_steps=["type_query"],
            confidence=0.9
        )
        
        engine = AIDecisionEngine()
        action_plan = await engine.plan_next_action(sample_navigator_request, intent)
        
        assert action_plan.next_action.action == ActionType.TYPE
        assert action_plan.next_action.text == "leather wallet"
        assert len(action_plan.alternative_actions) == 1
    
    @pytest.mark.asyncio
    async def test_plan_next_action_done_action(self, mock_openai_client, sample_navigator_request):
        """Test action planning for DONE action"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "current_step": 3,
            "total_steps": 3,
            "next_action": {
                "action": "DONE",
                "summary": "Search completed successfully"
            },
            "reasoning": "All required steps have been completed",
            "alternative_actions": []
        })
        
        intent = IntentAnalysis(
            primary_intent="SEARCH",
            entities=["wallet"],
            required_steps=["complete"],
            confidence=1.0
        )
        
        engine = AIDecisionEngine()
        action_plan = await engine.plan_next_action(sample_navigator_request, intent)
        
        assert action_plan.next_action.action == ActionType.DONE
        assert "completed successfully" in action_plan.next_action.summary
    
    @pytest.mark.asyncio
    async def test_plan_next_action_error_handling(self, mock_openai_client, sample_navigator_request):
        """Test action planning error handling"""
        mock_openai_client.chat.completions.create.side_effect = Exception("Planning Error")
        
        intent = IntentAnalysis(
            primary_intent="SEARCH",
            entities=[],
            required_steps=[],
            confidence=0.5
        )
        
        engine = AIDecisionEngine()
        action_plan = await engine.plan_next_action(sample_navigator_request, intent)
        
        # Should return fallback action plan
        assert action_plan.next_action.action == ActionType.DONE
        assert "error" in action_plan.next_action.summary.lower()
        assert "fallback" in action_plan.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_decide_action_full_workflow(self, mock_openai_client, sample_navigator_request):
        """Test the complete decision-making workflow"""
        # Mock intent analysis response
        intent_response = json.dumps({
            "primary_intent": "SEARCH",
            "entities": ["leather", "wallet"],
            "required_steps": ["click_search", "type_query"],
            "confidence": 0.9
        })
        
        # Mock action planning response
        planning_response = json.dumps({
            "current_step": 1,
            "total_steps": 2,
            "next_action": {
                "action": "CLICK",
                "elementId": 0
            },
            "reasoning": "Click search input to begin",
            "alternative_actions": []
        })
        
        # Set up mock to return different responses for different calls
        mock_openai_client.chat.completions.create.side_effect = [
            MagicMock(choices=[MagicMock(message=MagicMock(content=intent_response))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content=planning_response))])
        ]
        
        engine = AIDecisionEngine()
        response = await engine.decide_action(sample_navigator_request)
        
        assert response.action == ActionType.CLICK
        assert response.elementId == 0
        assert response.reasoning == "Click search input to begin"
        assert response.confidence == 0.9
        
        # Verify both OpenAI calls were made
        assert mock_openai_client.chat.completions.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_decide_action_with_complex_dom(self, mock_openai_client):
        """Test decision making with complex DOM structure"""
        complex_dom = [
            DOMElement(id=0, tag="nav", text="Navigation"),
            DOMElement(id=1, tag="input", text="", type="search", placeholder="Search products"),
            DOMElement(id=2, tag="button", text="Search"),
            DOMElement(id=3, tag="div", text="Featured Products"),
            DOMElement(id=4, tag="button", text="Add to Cart"),
            DOMElement(id=5, tag="button", text="Buy Now"),
            DOMElement(id=6, tag="a", text="View Details"),
            DOMElement(id=7, tag="select", text="Category"),
            DOMElement(id=8, tag="input", text="", type="email", placeholder="Newsletter"),
            DOMElement(id=9, tag="footer", text="Footer content")
        ]
        
        request = NavigatorRequest(
            query="find leather products and add the first one to cart",
            dom_snapshot=complex_dom,
            history=[]
        )
        
        # Mock responses
        intent_response = json.dumps({
            "primary_intent": "SEARCH_AND_ADD",
            "entities": ["leather", "products"],
            "required_steps": ["search", "select_product", "add_to_cart"],
            "confidence": 0.85
        })
        
        planning_response = json.dumps({
            "current_step": 1,
            "total_steps": 3,
            "next_action": {
                "action": "CLICK",
                "elementId": 1
            },
            "reasoning": "Click on search input to start finding leather products",
            "alternative_actions": []
        })
        
        mock_openai_client.chat.completions.create.side_effect = [
            MagicMock(choices=[MagicMock(message=MagicMock(content=intent_response))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content=planning_response))])
        ]
        
        engine = AIDecisionEngine()
        response = await engine.decide_action(request)
        
        assert response.action == ActionType.CLICK
        assert response.elementId == 1  # Search input
        
        # Verify the DOM was properly described in the request
        call_args = mock_openai_client.chat.completions.create.call_args_list[1]
        dom_description = call_args[1]["messages"][1]["content"]
        assert "input" in dom_description
        assert "search" in dom_description.lower()
    
    @pytest.mark.asyncio
    async def test_get_website_context(self, sample_dom_elements):
        """Test website context analysis"""
        engine = AIDecisionEngine()
        context = await engine.get_website_context(sample_dom_elements)
        
        assert context.page_type in ["unknown", "products", "home"]
        assert isinstance(context.available_actions, list)
        assert isinstance(context.common_patterns, dict)
        assert isinstance(context.navigation_structure, dict)
        
        # Should detect search functionality
        if any("search" in elem.text.lower() for elem in sample_dom_elements):
            assert "search" in context.available_actions
        
        # Should detect cart functionality
        if any("cart" in elem.text.lower() for elem in sample_dom_elements):
            assert "add_to_cart" in context.available_actions


class TestIntentAnalysisScenarios:
    """Test various intent analysis scenarios"""
    
    @pytest.mark.asyncio
    async def test_search_intent(self, mock_openai_client):
        """Test search intent recognition"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "primary_intent": "SEARCH",
            "entities": ["shoes", "nike"],
            "required_steps": ["open_search", "type_query", "submit"],
            "confidence": 0.95
        })
        
        engine = AIDecisionEngine()
        intent = await engine.analyze_intent("search for nike shoes", [])
        
        assert intent.primary_intent == "SEARCH"
        assert "shoes" in intent.entities
        assert "nike" in intent.entities
    
    @pytest.mark.asyncio
    async def test_add_to_cart_intent(self, mock_openai_client):
        """Test add to cart intent recognition"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "primary_intent": "ADD_TO_CART",
            "entities": ["this item", "cart"],
            "required_steps": ["click_add_to_cart"],
            "confidence": 0.9
        })
        
        engine = AIDecisionEngine()
        intent = await engine.analyze_intent("add this item to my cart", [])
        
        assert intent.primary_intent == "ADD_TO_CART"
        assert intent.confidence == 0.9
    
    @pytest.mark.asyncio
    async def test_checkout_intent(self, mock_openai_client):
        """Test checkout intent recognition"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "primary_intent": "CHECKOUT",
            "entities": ["checkout", "purchase"],
            "required_steps": ["go_to_cart", "proceed_to_checkout"],
            "confidence": 0.88
        })
        
        engine = AIDecisionEngine()
        intent = await engine.analyze_intent("proceed to checkout", [])
        
        assert intent.primary_intent == "CHECKOUT"
        assert len(intent.required_steps) == 2
    
    @pytest.mark.asyncio
    async def test_navigation_intent(self, mock_openai_client):
        """Test navigation intent recognition"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "primary_intent": "NAVIGATE",
            "entities": ["home page"],
            "required_steps": ["click_home_link"],
            "confidence": 0.85
        })
        
        engine = AIDecisionEngine()
        intent = await engine.analyze_intent("go to home page", [])
        
        assert intent.primary_intent == "NAVIGATE"
        assert "home page" in intent.entities
    
    @pytest.mark.asyncio
    async def test_complex_multi_step_intent(self, mock_openai_client):
        """Test complex multi-step intent"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "primary_intent": "SEARCH_AND_PURCHASE",
            "entities": ["leather wallet", "under $50", "purchase"],
            "required_steps": [
                "search_for_product",
                "apply_price_filter", 
                "select_product",
                "add_to_cart",
                "checkout"
            ],
            "confidence": 0.92
        })
        
        engine = AIDecisionEngine()
        intent = await engine.analyze_intent(
            "search for leather wallet under $50 and buy it", 
            []
        )
        
        assert intent.primary_intent == "SEARCH_AND_PURCHASE"
        assert len(intent.entities) == 3
        assert len(intent.required_steps) == 5
        assert intent.confidence == 0.92


class TestActionPlanningScenarios:
    """Test various action planning scenarios"""
    
    @pytest.mark.asyncio
    async def test_first_step_planning(self, mock_openai_client, sample_navigator_request):
        """Test planning the first step of an action sequence"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "current_step": 1,
            "total_steps": 4,
            "next_action": {
                "action": "CLICK",
                "elementId": 0
            },
            "reasoning": "Start by clicking the search input field",
            "alternative_actions": []
        })
        
        intent = IntentAnalysis(
            primary_intent="SEARCH",
            entities=["wallet"],
            required_steps=["click_search", "type_query", "submit", "select_result"],
            confidence=0.9
        )
        
        engine = AIDecisionEngine()
        plan = await engine.plan_next_action(sample_navigator_request, intent)
        
        assert plan.current_step == 1
        assert plan.total_steps == 4
        assert plan.next_action.action == ActionType.CLICK
    
    @pytest.mark.asyncio
    async def test_middle_step_planning(self, mock_openai_client):
        """Test planning a middle step with history"""
        request = NavigatorRequest(
            query="search for wallet",
            dom_snapshot=[
                DOMElement(id=0, tag="input", text="wallet", type="search"),
                DOMElement(id=1, tag="button", text="Search")
            ],
            history=[
                Action(action=ActionType.CLICK, elementId=0),
                Action(action=ActionType.TYPE, elementId=0, text="wallet")
            ]
        )
        
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "current_step": 3,
            "total_steps": 4,
            "next_action": {
                "action": "CLICK",
                "elementId": 1
            },
            "reasoning": "Now click the search button to execute the search",
            "alternative_actions": []
        })
        
        intent = IntentAnalysis(
            primary_intent="SEARCH",
            entities=["wallet"],
            required_steps=["submit_search"],
            confidence=0.9
        )
        
        engine = AIDecisionEngine()
        plan = await engine.plan_next_action(request, intent)
        
        assert plan.current_step == 3
        assert plan.next_action.action == ActionType.CLICK
        assert plan.next_action.elementId == 1  # Search button
    
    @pytest.mark.asyncio
    async def test_completion_step_planning(self, mock_openai_client, sample_navigator_request):
        """Test planning the final completion step"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "current_step": 4,
            "total_steps": 4,
            "next_action": {
                "action": "DONE",
                "summary": "Successfully searched for wallet and found results"
            },
            "reasoning": "All search steps completed, task is done",
            "alternative_actions": []
        })
        
        intent = IntentAnalysis(
            primary_intent="SEARCH",
            entities=["wallet"],
            required_steps=["complete"],
            confidence=1.0
        )
        
        engine = AIDecisionEngine()
        plan = await engine.plan_next_action(sample_navigator_request, intent)
        
        assert plan.current_step == 4
        assert plan.next_action.action == ActionType.DONE
        assert "successfully" in plan.next_action.summary.lower()
    
    @pytest.mark.asyncio
    async def test_planning_with_alternatives(self, mock_openai_client, sample_navigator_request):
        """Test action planning that includes alternative actions"""
        mock_openai_client.chat.completions.create.return_value.choices[0].message.content = json.dumps({
            "current_step": 2,
            "total_steps": 3,
            "next_action": {
                "action": "CLICK",
                "elementId": 5
            },
            "reasoning": "Click the primary Add to Cart button",
            "alternative_actions": [
                {"action": "CLICK", "elementId": 7},  # Buy Now button
                {"action": "CLICK", "elementId": 6}   # View Details
            ]
        })
        
        intent = IntentAnalysis(
            primary_intent="ADD_TO_CART",
            entities=["this item"],
            required_steps=["add_to_cart"],
            confidence=0.9
        )
        
        engine = AIDecisionEngine()
        plan = await engine.plan_next_action(sample_navigator_request, intent)
        
        assert plan.next_action.elementId == 5
        assert len(plan.alternative_actions) == 2
        assert plan.alternative_actions[0].elementId == 7
        assert plan.alternative_actions[1].elementId == 6
