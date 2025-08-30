"""
RAG (Retrieval-Augmented Generation) system for website understanding
"""

import json
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from models import DOMElement, WebsiteContext
from config import settings

logger = logging.getLogger(__name__)

class WebsiteRAGSystem:
    """RAG system for understanding website patterns and providing context"""
    
    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=Settings(allow_reset=True)
        )
        
        # Initialize collections
        self.patterns_collection = self._get_or_create_collection("website_patterns")
        self.actions_collection = self._get_or_create_collection("action_patterns")
        
        # Initialize with default e-commerce patterns
        self._initialize_default_patterns()
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection"""
        try:
            return self.chroma_client.get_collection(name)
        except Exception:
            return self.chroma_client.create_collection(name)
    
    def _initialize_default_patterns(self):
        """Initialize the RAG system with common e-commerce patterns"""
        
        # Check if patterns already exist
        try:
            existing = self.patterns_collection.get()
            if len(existing["ids"]) > 0:
                logger.info("Website patterns already initialized")
                return
        except Exception:
            pass
        
        # Default e-commerce patterns
        website_patterns = [
            {
                "id": "search_pattern_1",
                "pattern": "Search input field with placeholder 'Search products' or 'Search...'",
                "context": "product_search",
                "action_sequence": ["click_search_input", "type_search_term", "click_search_button"],
                "confidence": 0.9
            },
            {
                "id": "add_to_cart_pattern_1", 
                "pattern": "Button with text 'Add to Cart' or 'Add to Bag'",
                "context": "product_page",
                "action_sequence": ["click_add_to_cart"],
                "confidence": 0.95
            },
            {
                "id": "navigation_pattern_1",
                "pattern": "Navigation links like 'Home', 'Products', 'Cart', 'Checkout'",
                "context": "site_navigation",
                "action_sequence": ["click_nav_link"],
                "confidence": 0.8
            },
            {
                "id": "cart_pattern_1",
                "pattern": "Shopping cart icon or 'Cart' button with item count",
                "context": "cart_access",
                "action_sequence": ["click_cart_icon"],
                "confidence": 0.9
            },
            {
                "id": "checkout_pattern_1",
                "pattern": "Checkout button or 'Proceed to Checkout' link",
                "context": "checkout_process",
                "action_sequence": ["click_checkout_button"],
                "confidence": 0.95
            },
            {
                "id": "product_list_pattern_1",
                "pattern": "Grid of products with images, titles, and prices",
                "context": "product_listing",
                "action_sequence": ["click_product_item"],
                "confidence": 0.85
            }
        ]
        
        # Add patterns to vector database
        for pattern in website_patterns:
            self.add_website_pattern(
                pattern_id=pattern["id"],
                description=pattern["pattern"],
                context=pattern["context"],
                metadata={
                    "action_sequence": json.dumps(pattern["action_sequence"]),
                    "confidence": pattern["confidence"]
                }
            )
        
        # Default action patterns
        action_patterns = [
            {
                "id": "search_action_1",
                "intent": "search for products",
                "dom_indicators": ["input[type=search]", "search placeholder", "search button"],
                "action_sequence": [
                    {"action": "CLICK", "target": "search_input"},
                    {"action": "TYPE", "target": "search_input", "text": "search_term"},
                    {"action": "CLICK", "target": "search_button"}
                ]
            },
            {
                "id": "add_cart_action_1", 
                "intent": "add item to cart",
                "dom_indicators": ["Add to Cart button", "product page", "price display"],
                "action_sequence": [
                    {"action": "CLICK", "target": "add_to_cart_button"}
                ]
            },
            {
                "id": "checkout_action_1",
                "intent": "proceed to checkout",
                "dom_indicators": ["cart page", "checkout button", "cart items"],
                "action_sequence": [
                    {"action": "CLICK", "target": "checkout_button"}
                ]
            }
        ]
        
        # Add action patterns
        for pattern in action_patterns:
            self.add_action_pattern(
                pattern_id=pattern["id"],
                intent=pattern["intent"],
                dom_indicators=pattern["dom_indicators"],
                action_sequence=pattern["action_sequence"]
            )
        
        logger.info("Initialized RAG system with default e-commerce patterns")
    
    def add_website_pattern(
        self, 
        pattern_id: str, 
        description: str, 
        context: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Add a website pattern to the knowledge base"""
        
        embedding = self.embedding_model.encode([description])
        
        self.patterns_collection.add(
            embeddings=embedding.tolist(),
            documents=[description],
            metadatas=[{
                "context": context,
                **(metadata or {})
            }],
            ids=[pattern_id]
        )
    
    def add_action_pattern(
        self,
        pattern_id: str,
        intent: str,
        dom_indicators: List[str],
        action_sequence: List[Dict[str, Any]]
    ):
        """Add an action pattern to the knowledge base"""
        
        # Create a searchable description
        description = f"Intent: {intent}. DOM indicators: {', '.join(dom_indicators)}"
        embedding = self.embedding_model.encode([description])
        
        self.actions_collection.add(
            embeddings=embedding.tolist(),
            documents=[description],
            metadatas=[{
                "intent": intent,
                "dom_indicators": json.dumps(dom_indicators),
                "action_sequence": json.dumps(action_sequence)
            }],
            ids=[pattern_id]
        )
    
    def find_relevant_patterns(
        self, 
        query: str, 
        dom_elements: List[DOMElement],
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find relevant website patterns based on query and DOM state"""
        
        # Create search query combining user intent and DOM state
        dom_description = self._describe_dom_state(dom_elements)
        search_query = f"User query: {query}. Page elements: {dom_description}"
        
        # Get embedding for search query
        query_embedding = self.embedding_model.encode([search_query])
        
        # Search for relevant patterns
        results = self.patterns_collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        
        patterns = []
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            patterns.append({
                "description": doc,
                "context": metadata.get("context"),
                "action_sequence": metadata.get("action_sequence", []),
                "confidence": metadata.get("confidence", 0.5),
                "distance": results["distances"][0][i] if "distances" in results else 0
            })
        
        return patterns
    
    def find_action_patterns(
        self, 
        intent: str, 
        dom_elements: List[DOMElement],
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """Find relevant action patterns for a given intent"""
        
        dom_description = self._describe_dom_state(dom_elements)
        search_query = f"Intent: {intent}. Available elements: {dom_description}"
        
        query_embedding = self.embedding_model.encode([search_query])
        
        results = self.actions_collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        
        patterns = []
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i]
            patterns.append({
                "intent": metadata.get("intent"),
                "dom_indicators": metadata.get("dom_indicators", []),
                "action_sequence": metadata.get("action_sequence", []),
                "distance": results["distances"][0][i] if "distances" in results else 0
            })
        
        return patterns
    
    def _describe_dom_state(self, dom_elements: List[DOMElement]) -> str:
        """Create a text description of the current DOM state"""
        
        descriptions = []
        for element in dom_elements[:20]:  # Limit to first 20 elements
            desc = f"{element.tag}"
            if element.text:
                desc += f" '{element.text[:30]}'"
            if element.type:
                desc += f" (type: {element.type})"
            descriptions.append(desc)
        
        return "; ".join(descriptions)
    
    def get_enhanced_context(
        self, 
        query: str, 
        dom_elements: List[DOMElement]
    ) -> WebsiteContext:
        """Get enhanced website context using RAG"""
        
        # Find relevant patterns
        patterns = self.find_relevant_patterns(query, dom_elements)
        action_patterns = self.find_action_patterns(query, dom_elements)
        
        # Extract context information
        page_types = set()
        available_actions = set()
        common_patterns = {}
        
        for pattern in patterns:
            if pattern["context"]:
                page_types.add(pattern["context"])
            if pattern["action_sequence"]:
                available_actions.update(pattern["action_sequence"])
            
            common_patterns[pattern["context"]] = pattern["description"]
        
        # Determine most likely page type
        page_type = "unknown"
        if page_types:
            page_type = max(page_types, key=lambda x: len([p for p in patterns if p["context"] == x]))
        
        return WebsiteContext(
            page_type=page_type,
            available_actions=list(available_actions),
            common_patterns=common_patterns,
            navigation_structure={
                "rag_patterns": len(patterns),
                "action_patterns": len(action_patterns),
                "confidence": np.mean([p["confidence"] for p in patterns if "confidence" in p]) if patterns else 0.5
            }
        )
    
    def learn_from_interaction(
        self,
        query: str,
        dom_elements: List[DOMElement], 
        actions_taken: List[Dict[str, Any]],
        success: bool
    ):
        """Learn from successful/failed interactions to improve future decisions"""
        
        if not success:
            return
        
        # Create a new pattern from successful interaction
        pattern_id = f"learned_{hash(query + str(actions_taken))}"
        description = f"Successfully completed: {query}"
        
        # Extract context from the interaction
        context = "learned_pattern"
        action_sequence = [action.get("action", "unknown") for action in actions_taken]
        
        self.add_website_pattern(
            pattern_id=pattern_id,
            description=description,
            context=context,
            metadata={
                "action_sequence": json.dumps(action_sequence),
                "confidence": 0.8,
                "learned": True,
                "original_query": query
            }
        )
        
        logger.info(f"Learned new pattern from successful interaction: {pattern_id}")
    
    def reset_knowledge_base(self):
        """Reset the entire knowledge base (for testing/debugging)"""
        self.chroma_client.reset()
        self.patterns_collection = self._get_or_create_collection("website_patterns")
        self.actions_collection = self._get_or_create_collection("action_patterns")
        self._initialize_default_patterns()
        logger.info("Reset RAG knowledge base")
