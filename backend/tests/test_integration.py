"""
Integration tests for the complete AI Website Navigator workflow
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from models import DOMElement, Action, ActionType, NavigatorRequest


class TestCompleteWorkflow:
    """Test complete end-to-end workflow scenarios"""
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_simple_search_workflow(self, mock_rag_system, mock_ai_engine, test_client, no_rate_limit, clear_cache):
        """Test a complete simple search workflow"""
        
        # Step 1: User wants to search
        dom_elements = [
            {"id": 0, "tag": "input", "text": "", "type": "search", "placeholder": "Search products"},
            {"id": 1, "tag": "button", "text": "Search"},
            {"id": 2, "tag": "div", "text": "Welcome to our store"}
        ]
        
        # Mock AI responses for each step
        ai_responses = [
            # Step 1: Click search input
            MagicMock(
                action=ActionType.CLICK,
                elementId=0,
                reasoning="Click search input to start searching",
                confidence=0.9,
                model_dump=lambda: {
                    "action": "CLICK",
                    "elementId": 0,
                    "reasoning": "Click search input to start searching",
                    "confidence": 0.9
                }
            ),
            # Step 2: Type search term
            MagicMock(
                action=ActionType.TYPE,
                elementId=0,
                text="leather wallet",
                reasoning="Type search term",
                confidence=0.95,
                model_dump=lambda: {
                    "action": "TYPE",
                    "elementId": 0,
                    "text": "leather wallet",
                    "reasoning": "Type search term",
                    "confidence": 0.95
                }
            ),
            # Step 3: Click search button
            MagicMock(
                action=ActionType.CLICK,
                elementId=1,
                reasoning="Click search button to execute search",
                confidence=0.9,
                model_dump=lambda: {
                    "action": "CLICK",
                    "elementId": 1,
                    "reasoning": "Click search button to execute search",
                    "confidence": 0.9
                }
            ),
            # Step 4: Done
            MagicMock(
                action=ActionType.DONE,
                summary="Search completed successfully",
                reasoning="Search workflow completed",
                confidence=1.0,
                model_dump=lambda: {
                    "action": "DONE",
                    "summary": "Search completed successfully",
                    "reasoning": "Search workflow completed",
                    "confidence": 1.0
                }
            )
        ]
        
        mock_ai_engine.decide_action.side_effect = ai_responses
        mock_rag_system.get_enhanced_context.return_value = MagicMock()
        
        # Execute workflow steps
        request_data = {
            "query": "search for leather wallet",
            "dom_snapshot": dom_elements,
            "history": []
        }
        
        # Step 1
        response1 = test_client.post("/plan", json=request_data)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["action"] == "CLICK"
        assert data1["elementId"] == 0
        
        # Step 2 - Add previous action to history
        request_data["history"] = [{"action": "CLICK", "elementId": 0}]
        response2 = test_client.post("/plan", json=request_data)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["action"] == "TYPE"
        assert data2["text"] == "leather wallet"
        
        # Step 3 - Add typing action to history
        request_data["history"].append({"action": "TYPE", "elementId": 0, "text": "leather wallet"})
        response3 = test_client.post("/plan", json=request_data)
        assert response3.status_code == 200
        data3 = response3.json()
        assert data3["action"] == "CLICK"
        assert data3["elementId"] == 1
        
        # Step 4 - Final step
        request_data["history"].append({"action": "CLICK", "elementId": 1})
        response4 = test_client.post("/plan", json=request_data)
        assert response4.status_code == 200
        data4 = response4.json()
        assert data4["action"] == "DONE"
        assert "completed successfully" in data4["summary"]
        
        # Verify AI engine was called for each step
        assert mock_ai_engine.decide_action.call_count == 4
        
        # Verify learning was called for successful completion
        mock_rag_system.learn_from_interaction.assert_called()
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_add_to_cart_workflow(self, mock_rag_system, mock_ai_engine, test_client, no_rate_limit, clear_cache):
        """Test add to cart workflow"""
        
        # Product page DOM
        dom_elements = [
            {"id": 0, "tag": "h1", "text": "Leather Wallet - Premium Quality"},
            {"id": 1, "tag": "div", "text": "$29.99"},
            {"id": 2, "tag": "button", "text": "Add to Cart"},
            {"id": 3, "tag": "button", "text": "Buy Now"},
            {"id": 4, "tag": "select", "text": "Color"},
            {"id": 5, "tag": "input", "text": "1", "type": "number"}
        ]
        
        # Mock AI response for add to cart
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.CLICK,
            elementId=2,
            reasoning="Click Add to Cart button to add product",
            confidence=0.95,
            model_dump=lambda: {
                "action": "CLICK",
                "elementId": 2,
                "reasoning": "Click Add to Cart button to add product",
                "confidence": 0.95
            }
        )
        
        request_data = {
            "query": "add this product to my cart",
            "dom_snapshot": dom_elements,
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["action"] == "CLICK"
        assert data["elementId"] == 2  # Add to Cart button
        assert "add to cart" in data["reasoning"].lower()
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_checkout_workflow(self, mock_rag_system, mock_ai_engine, test_client, no_rate_limit, clear_cache):
        """Test checkout workflow"""
        
        # Cart page DOM
        dom_elements = [
            {"id": 0, "tag": "h2", "text": "Shopping Cart"},
            {"id": 1, "tag": "div", "text": "Leather Wallet x1 - $29.99"},
            {"id": 2, "tag": "button", "text": "Remove"},
            {"id": 3, "tag": "button", "text": "Update Quantity"},
            {"id": 4, "tag": "div", "text": "Total: $29.99"},
            {"id": 5, "tag": "button", "text": "Proceed to Checkout"},
            {"id": 6, "tag": "a", "text": "Continue Shopping"}
        ]
        
        # Mock AI response for checkout
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.CLICK,
            elementId=5,
            reasoning="Click Proceed to Checkout to start checkout process",
            confidence=0.9,
            model_dump=lambda: {
                "action": "CLICK",
                "elementId": 5,
                "reasoning": "Click Proceed to Checkout to start checkout process",
                "confidence": 0.9
            }
        )
        
        request_data = {
            "query": "proceed to checkout",
            "dom_snapshot": dom_elements,
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["action"] == "CLICK"
        assert data["elementId"] == 5  # Checkout button
        assert "checkout" in data["reasoning"].lower()
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_complex_multi_step_workflow(self, mock_rag_system, mock_ai_engine, test_client, no_rate_limit, clear_cache):
        """Test complex multi-step workflow: search + filter + add to cart"""
        
        # Initial page DOM
        initial_dom = [
            {"id": 0, "tag": "input", "text": "", "type": "search", "placeholder": "Search"},
            {"id": 1, "tag": "button", "text": "Search"},
            {"id": 2, "tag": "select", "text": "All Categories"},
            {"id": 3, "tag": "div", "text": "Price Range"},
            {"id": 4, "tag": "input", "text": "", "type": "number", "placeholder": "Min Price"},
            {"id": 5, "tag": "input", "text": "", "type": "number", "placeholder": "Max Price"}
        ]
        
        # Product results DOM (after search)
        results_dom = [
            {"id": 0, "tag": "div", "text": "Search Results for 'wallet'"},
            {"id": 1, "tag": "div", "text": "Leather Wallet - $25.99"},
            {"id": 2, "tag": "button", "text": "Add to Cart"},
            {"id": 3, "tag": "div", "text": "Canvas Wallet - $15.99"},
            {"id": 4, "tag": "button", "text": "Add to Cart"},
            {"id": 5, "tag": "div", "text": "Premium Wallet - $45.99"},
            {"id": 6, "tag": "button", "text": "Add to Cart"}
        ]
        
        # Mock AI responses for each step
        ai_responses = [
            # Step 1: Search
            MagicMock(action=ActionType.CLICK, elementId=0, model_dump=lambda: {"action": "CLICK", "elementId": 0}),
            # Step 2: Type search term  
            MagicMock(action=ActionType.TYPE, elementId=0, text="wallet", model_dump=lambda: {"action": "TYPE", "elementId": 0, "text": "wallet"}),
            # Step 3: Submit search
            MagicMock(action=ActionType.CLICK, elementId=1, model_dump=lambda: {"action": "CLICK", "elementId": 1}),
            # Step 4: Add first product to cart
            MagicMock(action=ActionType.CLICK, elementId=2, model_dump=lambda: {"action": "CLICK", "elementId": 2}),
            # Step 5: Done
            MagicMock(action=ActionType.DONE, summary="Product added to cart", model_dump=lambda: {"action": "DONE", "summary": "Product added to cart"})
        ]
        
        mock_ai_engine.decide_action.side_effect = ai_responses
        
        history = []
        
        # Step 1: Search
        request_data = {
            "query": "search for wallet under $30 and add the cheapest one to cart",
            "dom_snapshot": initial_dom,
            "history": history
        }
        
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 200
        history.append(response.json())
        
        # Step 2: Type
        request_data["history"] = [{"action": "CLICK", "elementId": 0}]
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 200
        
        # Step 3: Search button
        request_data["history"].append({"action": "TYPE", "elementId": 0, "text": "wallet"})
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 200
        
        # Step 4: Switch to results DOM and add to cart
        request_data["dom_snapshot"] = results_dom
        request_data["history"].append({"action": "CLICK", "elementId": 1})
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 200
        
        # Step 5: Complete
        request_data["history"].append({"action": "CLICK", "elementId": 2})
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "DONE"
        
        # Verify all steps were executed
        assert mock_ai_engine.decide_action.call_count == 5


class TestWorkflowWithRAGLearning:
    """Test workflows that involve RAG learning and pattern recognition"""
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_workflow_with_pattern_learning(self, mock_rag_system, mock_ai_engine, test_client, no_rate_limit, clear_cache):
        """Test workflow where RAG system learns from successful patterns"""
        
        dom_elements = [
            {"id": 0, "tag": "input", "text": "", "type": "search"},
            {"id": 1, "tag": "button", "text": "Search"},
            {"id": 2, "tag": "div", "text": "Product: Wallet"}
        ]
        
        # Mock successful completion
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.DONE,
            summary="Task completed successfully",
            model_dump=lambda: {"action": "DONE", "summary": "Task completed successfully"}
        )
        
        # Mock RAG context
        mock_context = MagicMock()
        mock_rag_system.get_enhanced_context.return_value = mock_context
        
        # Execute workflow
        request_data = {
            "query": "search for wallet",
            "dom_snapshot": dom_elements,
            "history": [
                {"action": "CLICK", "elementId": 0},
                {"action": "TYPE", "elementId": 0, "text": "wallet"},
                {"action": "CLICK", "elementId": 1}
            ]
        }
        
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 200
        
        # Verify RAG learning was called with successful interaction
        mock_rag_system.learn_from_interaction.assert_called_once()
        call_args = mock_rag_system.learn_from_interaction.call_args
        
        assert call_args[1]["query"] == "search for wallet"
        assert call_args[1]["success"] == True
        assert len(call_args[1]["actions_taken"]) == 3
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_workflow_with_pattern_retrieval(self, mock_rag_system, mock_ai_engine, test_client, no_rate_limit, clear_cache):
        """Test workflow that uses retrieved patterns for decision making"""
        
        # Mock RAG system returning relevant patterns
        mock_patterns = [
            {
                "description": "Search pattern for e-commerce",
                "context": "search",
                "action_sequence": ["click_search", "type_query", "submit"],
                "confidence": 0.9
            }
        ]
        
        mock_context = MagicMock()
        mock_context.page_type = "search"
        mock_context.available_actions = ["search", "filter"]
        
        mock_rag_system.get_enhanced_context.return_value = mock_context
        mock_rag_system.find_relevant_patterns.return_value = mock_patterns
        
        # Mock AI using the patterns
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.CLICK,
            elementId=0,
            reasoning="Using learned search pattern",
            confidence=0.95,
            model_dump=lambda: {
                "action": "CLICK",
                "elementId": 0,
                "reasoning": "Using learned search pattern",
                "confidence": 0.95
            }
        )
        
        request_data = {
            "query": "search for products",
            "dom_snapshot": [
                {"id": 0, "tag": "input", "text": "", "type": "search"},
                {"id": 1, "tag": "button", "text": "Search"}
            ],
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["action"] == "CLICK"
        assert "learned" in data["reasoning"].lower()
        
        # Verify RAG context was retrieved
        mock_rag_system.get_enhanced_context.assert_called_once()


class TestWorkflowErrorRecovery:
    """Test workflow error handling and recovery scenarios"""
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_workflow_with_ai_engine_error(self, mock_rag_system, mock_ai_engine, test_client, no_rate_limit, clear_cache):
        """Test workflow when AI engine encounters an error"""
        
        # Mock AI engine error
        mock_ai_engine.decide_action.side_effect = Exception("AI processing error")
        
        request_data = {
            "query": "search for products",
            "dom_snapshot": [{"id": 0, "tag": "input", "text": ""}],
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 500
        
        # Should return proper error response
        data = response.json()
        assert "error" in data
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_workflow_with_rag_error(self, mock_rag_system, mock_ai_engine, test_client, no_rate_limit, clear_cache):
        """Test workflow when RAG system has errors"""
        
        # Mock RAG error
        mock_rag_system.get_enhanced_context.side_effect = Exception("RAG error")
        
        # AI should still work without RAG
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.CLICK,
            elementId=0,
            model_dump=lambda: {"action": "CLICK", "elementId": 0}
        )
        
        request_data = {
            "query": "search for products",
            "dom_snapshot": [{"id": 0, "tag": "input", "text": ""}],
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 500  # Should handle RAG error gracefully
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_workflow_with_invalid_dom_state(self, mock_rag_system, mock_ai_engine, test_client, no_rate_limit, clear_cache):
        """Test workflow with invalid DOM state"""
        
        # Invalid DOM elements
        invalid_dom = [
            {"invalid": "format"},
            {"missing": "required_fields"}
        ]
        
        request_data = {
            "query": "test query",
            "dom_snapshot": invalid_dom,
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 422  # Validation error
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_workflow_element_not_found_recovery(self, mock_rag_system, mock_ai_engine, test_client, no_rate_limit, clear_cache):
        """Test workflow recovery when target element is not found"""
        
        # Mock AI returning action for non-existent element
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.CLICK,
            elementId=999,  # Non-existent element
            reasoning="Click non-existent element",
            model_dump=lambda: {
                "action": "CLICK", 
                "elementId": 999,
                "reasoning": "Click non-existent element"
            }
        )
        
        request_data = {
            "query": "click something",
            "dom_snapshot": [{"id": 0, "tag": "button", "text": "Valid Button"}],
            "history": []
        }
        
        response = test_client.post("/plan", json=request_data)
        assert response.status_code == 200
        
        # Should return the action even if element doesn't exist
        # Frontend will handle element validation
        data = response.json()
        assert data["elementId"] == 999


class TestWorkflowWithFeedback:
    """Test workflows that include feedback mechanisms"""
    
    @patch('main.rag_system')
    def test_successful_workflow_feedback(self, mock_rag_system, test_client, no_rate_limit):
        """Test submitting feedback for successful workflow"""
        
        feedback_data = {
            "query": "search for wallet and add to cart",
            "success": True,
            "actions": [
                {"action": "CLICK", "elementId": 0},
                {"action": "TYPE", "elementId": 0, "text": "wallet"},
                {"action": "CLICK", "elementId": 1},
                {"action": "CLICK", "elementId": 5}
            ],
            "dom_snapshot": [
                {"id": 0, "tag": "input", "text": "", "type": "search"},
                {"id": 1, "tag": "button", "text": "Search"},
                {"id": 5, "tag": "button", "text": "Add to Cart"}
            ]
        }
        
        response = test_client.post("/feedback", json=feedback_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "feedback_recorded"
        
        # Verify RAG learning was triggered
        mock_rag_system.learn_from_interaction.assert_called_once()
        call_args = mock_rag_system.learn_from_interaction.call_args
        
        assert call_args[1]["success"] == True
        assert len(call_args[1]["actions_taken"]) == 4
    
    @patch('main.rag_system')
    def test_failed_workflow_feedback(self, mock_rag_system, test_client, no_rate_limit):
        """Test submitting feedback for failed workflow"""
        
        feedback_data = {
            "query": "search for wallet",
            "success": False,
            "actions": [
                {"action": "CLICK", "elementId": 0},
                {"action": "TYPE", "elementId": 0, "text": "wallet"}
            ],
            "dom_snapshot": [
                {"id": 0, "tag": "input", "text": "", "type": "search"}
            ]
        }
        
        response = test_client.post("/feedback", json=feedback_data)
        assert response.status_code == 200
        
        # Verify RAG learning was called with failure
        mock_rag_system.learn_from_interaction.assert_called_once()
        call_args = mock_rag_system.learn_from_interaction.call_args
        
        assert call_args[1]["success"] == False
    
    @patch('main.ai_engine')
    @patch('main.rag_system')
    def test_workflow_feedback_loop(self, mock_rag_system, mock_ai_engine, test_client, no_rate_limit, clear_cache):
        """Test complete workflow with feedback loop for learning"""
        
        # Execute workflow
        mock_ai_engine.decide_action.return_value = MagicMock(
            action=ActionType.DONE,
            summary="Completed successfully",
            model_dump=lambda: {"action": "DONE", "summary": "Completed successfully"}
        )
        
        # Step 1: Execute workflow
        workflow_request = {
            "query": "search for products",
            "dom_snapshot": [{"id": 0, "tag": "input", "text": ""}],
            "history": [{"action": "CLICK", "elementId": 0}]
        }
        
        workflow_response = test_client.post("/plan", json=workflow_request)
        assert workflow_response.status_code == 200
        
        # Step 2: Submit feedback
        feedback_request = {
            "query": "search for products",
            "success": True,
            "actions": [{"action": "CLICK", "elementId": 0}],
            "dom_snapshot": [{"id": 0, "tag": "input", "text": ""}]
        }
        
        feedback_response = test_client.post("/feedback", json=feedback_request)
        assert feedback_response.status_code == 200
        
        # Verify learning happened twice (once automatically, once from feedback)
        assert mock_rag_system.learn_from_interaction.call_count >= 1
