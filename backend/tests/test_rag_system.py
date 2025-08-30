"""
Tests for the RAG (Retrieval-Augmented Generation) System
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from rag_system import WebsiteRAGSystem
from models import DOMElement, WebsiteContext


class TestWebsiteRAGSystem:
    """Test the main RAG system functionality"""
    
    @patch('rag_system.chromadb')
    @patch('rag_system.SentenceTransformer')
    def test_rag_system_initialization(self, mock_transformer, mock_chromadb):
        """Test RAG system initialization"""
        # Mock dependencies
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": []}
        
        mock_client.get_collection.side_effect = Exception("Not found")
        mock_client.create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client
        
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_transformer.return_value = mock_model
        
        rag_system = WebsiteRAGSystem()
        
        assert rag_system is not None
        assert rag_system.embedding_model is not None
        assert rag_system.chroma_client is not None
    
    @patch('rag_system.chromadb')
    @patch('rag_system.SentenceTransformer')
    def test_rag_system_existing_patterns(self, mock_transformer, mock_chromadb):
        """Test RAG system with existing patterns"""
        # Mock existing patterns
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": ["pattern1", "pattern2"]}
        
        mock_client.get_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client
        
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        rag_system = WebsiteRAGSystem()
        
        # Should not reinitialize patterns since they already exist
        mock_collection.add.assert_not_called()
    
    def test_describe_dom_state(self, mock_chromadb, mock_sentence_transformer, sample_dom_elements):
        """Test DOM state description generation"""
        rag_system = WebsiteRAGSystem()
        description = rag_system._describe_dom_state(sample_dom_elements)
        
        assert isinstance(description, str)
        assert len(description) > 0
        
        # Should contain information about the DOM elements
        assert "input" in description
        assert "button" in description
        
        # Should limit to first 20 elements and truncate text
        long_dom = [DOMElement(id=i, tag="div", text=f"Very long text content for element {i} " * 10) 
                   for i in range(30)]
        long_description = rag_system._describe_dom_state(long_dom)
        
        # Should be limited and truncated
        assert len(long_description.split("; ")) <= 20
    
    def test_add_website_pattern(self, mock_chromadb, mock_sentence_transformer):
        """Test adding website patterns"""
        rag_system = WebsiteRAGSystem()
        
        # Mock the collection
        mock_collection = rag_system.patterns_collection
        
        rag_system.add_website_pattern(
            pattern_id="test_pattern",
            description="Test search pattern",
            context="search",
            metadata={"confidence": 0.9}
        )
        
        # Verify add was called
        mock_collection.add.assert_called()
        call_args = mock_collection.add.call_args
        
        assert "test_pattern" in call_args[1]["ids"]
        assert "Test search pattern" in call_args[1]["documents"]
        assert call_args[1]["metadatas"][0]["context"] == "search"
        assert call_args[1]["metadatas"][0]["confidence"] == 0.9
    
    def test_add_action_pattern(self, mock_chromadb, mock_sentence_transformer):
        """Test adding action patterns"""
        rag_system = WebsiteRAGSystem()
        
        # Mock the collection
        mock_collection = rag_system.actions_collection
        
        dom_indicators = ["search input", "search button"]
        action_sequence = [{"action": "CLICK", "target": "search_input"}]
        
        rag_system.add_action_pattern(
            pattern_id="search_action",
            intent="search for products",
            dom_indicators=dom_indicators,
            action_sequence=action_sequence
        )
        
        # Verify add was called
        mock_collection.add.assert_called()
        call_args = mock_collection.add.call_args
        
        assert "search_action" in call_args[1]["ids"]
        assert call_args[1]["metadatas"][0]["intent"] == "search for products"
        assert call_args[1]["metadatas"][0]["dom_indicators"] == dom_indicators
        assert call_args[1]["metadatas"][0]["action_sequence"] == action_sequence
    
    def test_find_relevant_patterns(self, mock_chromadb, mock_sentence_transformer, sample_dom_elements):
        """Test finding relevant patterns"""
        rag_system = WebsiteRAGSystem()
        
        # Mock the collection query response
        mock_collection = rag_system.patterns_collection
        mock_collection.query.return_value = {
            "documents": [["Search pattern description", "Cart pattern description"]],
            "metadatas": [[
                {"context": "search", "action_sequence": ["click_search"], "confidence": 0.9},
                {"context": "cart", "action_sequence": ["click_cart"], "confidence": 0.8}
            ]],
            "distances": [[0.1, 0.3]]
        }
        
        patterns = rag_system.find_relevant_patterns(
            "search for products", 
            sample_dom_elements[:3],
            n_results=2
        )
        
        assert len(patterns) == 2
        assert patterns[0]["context"] == "search"
        assert patterns[0]["confidence"] == 0.9
        assert patterns[0]["distance"] == 0.1
        assert patterns[1]["context"] == "cart"
        
        # Verify query was called with correct parameters
        mock_collection.query.assert_called_once()
        call_args = mock_collection.query.call_args[1]
        assert call_args["n_results"] == 2
    
    def test_find_action_patterns(self, mock_chromadb, mock_sentence_transformer, sample_dom_elements):
        """Test finding action patterns"""
        rag_system = WebsiteRAGSystem()
        
        # Mock the collection query response
        mock_collection = rag_system.actions_collection
        mock_collection.query.return_value = {
            "documents": [["Search action pattern"]],
            "metadatas": [[{
                "intent": "search",
                "dom_indicators": ["search input", "search button"],
                "action_sequence": [{"action": "CLICK", "target": "search"}]
            }]],
            "distances": [[0.15]]
        }
        
        patterns = rag_system.find_action_patterns(
            "search",
            sample_dom_elements,
            n_results=1
        )
        
        assert len(patterns) == 1
        assert patterns[0]["intent"] == "search"
        assert "search input" in patterns[0]["dom_indicators"]
        assert patterns[0]["distance"] == 0.15
    
    def test_get_enhanced_context(self, mock_chromadb, mock_sentence_transformer, sample_dom_elements):
        """Test enhanced context generation"""
        rag_system = WebsiteRAGSystem()
        
        # Mock pattern and action pattern responses
        mock_patterns_collection = rag_system.patterns_collection
        mock_actions_collection = rag_system.actions_collection
        
        mock_patterns_collection.query.return_value = {
            "documents": [["Search functionality", "Cart functionality"]],
            "metadatas": [[
                {"context": "search", "action_sequence": ["search"], "confidence": 0.9},
                {"context": "cart", "action_sequence": ["add_to_cart"], "confidence": 0.8}
            ]],
            "distances": [[0.1, 0.2]]
        }
        
        mock_actions_collection.query.return_value = {
            "documents": [["Action pattern"]],
            "metadatas": [[{
                "intent": "search",
                "dom_indicators": ["input"],
                "action_sequence": [{"action": "CLICK"}]
            }]],
            "distances": [[0.1]]
        }
        
        context = rag_system.get_enhanced_context("search for products", sample_dom_elements)
        
        assert isinstance(context, WebsiteContext)
        assert context.page_type in ["search", "cart", "unknown"]
        assert isinstance(context.available_actions, list)
        assert isinstance(context.common_patterns, dict)
        assert "rag_patterns" in context.navigation_structure
        assert "confidence" in context.navigation_structure
    
    def test_learn_from_interaction_success(self, mock_chromadb, mock_sentence_transformer, sample_dom_elements):
        """Test learning from successful interactions"""
        rag_system = WebsiteRAGSystem()
        
        actions_taken = [
            {"action": "CLICK", "elementId": 0},
            {"action": "TYPE", "elementId": 0, "text": "wallet"},
            {"action": "CLICK", "elementId": 1}
        ]
        
        rag_system.learn_from_interaction(
            query="search for wallet",
            dom_elements=sample_dom_elements,
            actions_taken=actions_taken,
            success=True
        )
        
        # Should add a new pattern for successful interaction
        mock_collection = rag_system.patterns_collection
        mock_collection.add.assert_called()
        
        call_args = mock_collection.add.call_args[1]
        assert "learned_" in call_args["ids"][0]
        assert "Successfully completed" in call_args["documents"][0]
        assert call_args["metadatas"][0]["learned"] == True
        assert call_args["metadatas"][0]["original_query"] == "search for wallet"
    
    def test_learn_from_interaction_failure(self, mock_chromadb, mock_sentence_transformer, sample_dom_elements):
        """Test that failed interactions are not learned from"""
        rag_system = WebsiteRAGSystem()
        
        actions_taken = [{"action": "CLICK", "elementId": 0}]
        
        rag_system.learn_from_interaction(
            query="failed query",
            dom_elements=sample_dom_elements,
            actions_taken=actions_taken,
            success=False
        )
        
        # Should not add any patterns for failed interactions
        mock_collection = rag_system.patterns_collection
        # Only the initialization calls should have happened
        initial_call_count = mock_collection.add.call_count
        
        # Call again to ensure no additional calls
        rag_system.learn_from_interaction(
            query="another failed query",
            dom_elements=sample_dom_elements,
            actions_taken=actions_taken,
            success=False
        )
        
        assert mock_collection.add.call_count == initial_call_count
    
    def test_reset_knowledge_base(self, mock_chromadb, mock_sentence_transformer):
        """Test resetting the knowledge base"""
        rag_system = WebsiteRAGSystem()
        
        # Mock the client reset and recreation
        mock_client = rag_system.chroma_client
        mock_collection = MagicMock()
        mock_collection.get.return_value = {"ids": []}
        
        # Reset method should recreate collections
        with patch.object(rag_system, '_get_or_create_collection') as mock_get_create:
            mock_get_create.return_value = mock_collection
            
            rag_system.reset_knowledge_base()
            
            # Should reset client and recreate collections
            mock_client.reset.assert_called_once()
            assert mock_get_create.call_count >= 2  # patterns and actions collections


class TestRAGPatternMatching:
    """Test pattern matching and similarity functionality"""
    
    def test_pattern_similarity_search(self, mock_chromadb, mock_sentence_transformer, sample_dom_elements):
        """Test pattern similarity search with various queries"""
        rag_system = WebsiteRAGSystem()
        
        # Mock different similarity scores for different patterns
        mock_collection = rag_system.patterns_collection
        mock_collection.query.return_value = {
            "documents": [["High relevance pattern", "Medium relevance pattern", "Low relevance pattern"]],
            "metadatas": [[
                {"context": "search", "confidence": 0.95, "action_sequence": ["search"]},
                {"context": "navigation", "confidence": 0.7, "action_sequence": ["navigate"]},
                {"context": "other", "confidence": 0.3, "action_sequence": ["other"]}
            ]],
            "distances": [[0.05, 0.3, 0.8]]  # Lower distance = higher similarity
        }
        
        patterns = rag_system.find_relevant_patterns(
            "search for products",
            sample_dom_elements,
            n_results=3
        )
        
        # Should return patterns sorted by relevance (distance)
        assert len(patterns) == 3
        assert patterns[0]["distance"] == 0.05  # Highest similarity
        assert patterns[0]["confidence"] == 0.95
        assert patterns[2]["distance"] == 0.8   # Lowest similarity
    
    def test_context_specific_patterns(self, mock_chromadb, mock_sentence_transformer):
        """Test context-specific pattern retrieval"""
        rag_system = WebsiteRAGSystem()
        
        # Test with e-commerce specific elements
        ecommerce_elements = [
            DOMElement(id=0, tag="input", text="", type="search", placeholder="Search products"),
            DOMElement(id=1, tag="button", text="Add to Cart"),
            DOMElement(id=2, tag="div", text="$29.99"),
            DOMElement(id=3, tag="button", text="Buy Now"),
            DOMElement(id=4, tag="select", text="Size"),
            DOMElement(id=5, tag="a", text="Checkout")
        ]
        
        mock_collection = rag_system.patterns_collection
        mock_collection.query.return_value = {
            "documents": [["E-commerce search pattern", "Shopping cart pattern"]],
            "metadatas": [[
                {"context": "product_search", "confidence": 0.9},
                {"context": "shopping_cart", "confidence": 0.85}
            ]],
            "distances": [[0.1, 0.2]]
        }
        
        patterns = rag_system.find_relevant_patterns(
            "add product to cart",
            ecommerce_elements,
            n_results=2
        )
        
        assert len(patterns) == 2
        assert any(p["context"] == "product_search" for p in patterns)
        assert any(p["context"] == "shopping_cart" for p in patterns)
    
    def test_action_sequence_matching(self, mock_chromadb, mock_sentence_transformer, sample_dom_elements):
        """Test matching action sequences to intents"""
        rag_system = WebsiteRAGSystem()
        
        mock_collection = rag_system.actions_collection
        mock_collection.query.return_value = {
            "documents": [["Multi-step search action"]],
            "metadatas": [[{
                "intent": "search_and_select",
                "dom_indicators": ["search input", "product list", "add to cart"],
                "action_sequence": [
                    {"action": "CLICK", "target": "search_input"},
                    {"action": "TYPE", "target": "search_input", "text": "query"},
                    {"action": "CLICK", "target": "search_button"},
                    {"action": "CLICK", "target": "product_item"},
                    {"action": "CLICK", "target": "add_to_cart"}
                ]
            }]],
            "distances": [[0.1]]
        }
        
        patterns = rag_system.find_action_patterns(
            "search for product and add to cart",
            sample_dom_elements
        )
        
        assert len(patterns) == 1
        assert patterns[0]["intent"] == "search_and_select"
        assert len(patterns[0]["action_sequence"]) == 5
        assert patterns[0]["action_sequence"][0]["action"] == "CLICK"
        assert patterns[0]["action_sequence"][1]["action"] == "TYPE"


class TestRAGLearningMechanisms:
    """Test RAG learning and adaptation mechanisms"""
    
    def test_pattern_extraction_from_success(self, mock_chromadb, mock_sentence_transformer, sample_dom_elements):
        """Test extracting patterns from successful interactions"""
        rag_system = WebsiteRAGSystem()
        
        # Simulate a successful search interaction
        successful_actions = [
            {"action": "CLICK", "elementId": 0, "description": "clicked search input"},
            {"action": "TYPE", "elementId": 0, "text": "leather wallet"},
            {"action": "CLICK", "elementId": 1, "description": "clicked search button"},
            {"action": "CLICK", "elementId": 6, "description": "clicked product"},
            {"action": "CLICK", "elementId": 5, "description": "added to cart"}
        ]
        
        rag_system.learn_from_interaction(
            query="search for leather wallet and add to cart",
            dom_elements=sample_dom_elements,
            actions_taken=successful_actions,
            success=True
        )
        
        # Verify the pattern was learned
        mock_collection = rag_system.patterns_collection
        call_args = mock_collection.add.call_args[1]
        
        # Should extract meaningful action sequence
        learned_metadata = call_args["metadatas"][0]
        assert learned_metadata["learned"] == True
        assert len(learned_metadata["action_sequence"]) == 5
        assert "CLICK" in learned_metadata["action_sequence"]
        assert "TYPE" in learned_metadata["action_sequence"]
    
    def test_incremental_learning(self, mock_chromadb, mock_sentence_transformer, sample_dom_elements):
        """Test incremental learning from multiple interactions"""
        rag_system = WebsiteRAGSystem()
        
        # Learn from multiple similar successful interactions
        interactions = [
            {
                "query": "search for shoes",
                "actions": [{"action": "CLICK", "elementId": 0}, {"action": "TYPE", "elementId": 0, "text": "shoes"}]
            },
            {
                "query": "search for jackets", 
                "actions": [{"action": "CLICK", "elementId": 0}, {"action": "TYPE", "elementId": 0, "text": "jackets"}]
            },
            {
                "query": "search for accessories",
                "actions": [{"action": "CLICK", "elementId": 0}, {"action": "TYPE", "elementId": 0, "text": "accessories"}]
            }
        ]
        
        for interaction in interactions:
            rag_system.learn_from_interaction(
                query=interaction["query"],
                dom_elements=sample_dom_elements,
                actions_taken=interaction["actions"],
                success=True
            )
        
        # Should have learned from all interactions
        mock_collection = rag_system.patterns_collection
        assert mock_collection.add.call_count >= len(interactions)
    
    def test_pattern_confidence_evolution(self, mock_chromadb, mock_sentence_transformer, sample_dom_elements):
        """Test how pattern confidence evolves with learning"""
        rag_system = WebsiteRAGSystem()
        
        # Learn a pattern multiple times (simulating repeated success)
        for i in range(3):
            rag_system.learn_from_interaction(
                query=f"search for product {i}",
                dom_elements=sample_dom_elements,
                actions_taken=[{"action": "CLICK", "elementId": 0}],
                success=True
            )
        
        # All learned patterns should have reasonable confidence
        mock_collection = rag_system.patterns_collection
        call_args_list = mock_collection.add.call_args_list
        
        for call_args in call_args_list:
            metadata = call_args[1]["metadatas"][0]
            if "learned" in metadata and metadata["learned"]:
                assert metadata["confidence"] == 0.8  # Default learned confidence
    
    def test_pattern_diversity(self, mock_chromadb, mock_sentence_transformer):
        """Test learning diverse patterns for different contexts"""
        rag_system = WebsiteRAGSystem()
        
        # Different contexts with different DOM structures
        contexts = [
            {
                "query": "search for products",
                "elements": [
                    DOMElement(id=0, tag="input", text="", type="search"),
                    DOMElement(id=1, tag="button", text="Search")
                ],
                "actions": [{"action": "CLICK", "elementId": 0}]
            },
            {
                "query": "add to cart",
                "elements": [
                    DOMElement(id=0, tag="button", text="Add to Cart"),
                    DOMElement(id=1, tag="div", text="$19.99")
                ],
                "actions": [{"action": "CLICK", "elementId": 0}]
            },
            {
                "query": "checkout",
                "elements": [
                    DOMElement(id=0, tag="a", text="Checkout"),
                    DOMElement(id=1, tag="form", text="Payment form")
                ],
                "actions": [{"action": "CLICK", "elementId": 0}]
            }
        ]
        
        for context in contexts:
            rag_system.learn_from_interaction(
                query=context["query"],
                dom_elements=context["elements"],
                actions_taken=context["actions"],
                success=True
            )
        
        # Should learn different patterns for different contexts
        mock_collection = rag_system.patterns_collection
        assert mock_collection.add.call_count >= len(contexts)
        
        # Each pattern should have unique characteristics
        call_args_list = mock_collection.add.call_args_list
        learned_queries = []
        for call_args in call_args_list:
            metadata = call_args[1]["metadatas"][0]
            if "original_query" in metadata:
                learned_queries.append(metadata["original_query"])
        
        # Should have learned from all different queries
        unique_queries = set(learned_queries)
        assert len(unique_queries) >= 3
