"""
Metadata Discovery Agent using LangGraph
Automatically discovers and extracts metadata from legal document sources
"""

import json
import logging
from typing import TypedDict, Annotated, List, Dict, Any
from datetime import datetime
from pathlib import Path

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.config import config
from src.tools.web_scraper import (
    fetch_webpage,
    search_vanban_chinhphu,
    extract_document_metadata,
    filter_relevant_documents
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define the State for our agent
class MetadataDiscoveryState(TypedDict):
    """State for metadata discovery agent"""
    
    # Input
    keywords: List[str]
    source: str
    max_documents: int
    
    # Processing
    raw_documents: List[Dict[str, Any]]
    filtered_documents: List[Dict[str, Any]]
    metadata_list: List[Dict[str, Any]]
    
    # Output
    saved_metadata_path: str
    total_discovered: int
    total_relevant: int
    
    # Agent state
    current_step: str
    messages: List[Any]
    error: str


class MetadataDiscoveryAgent:
    """
    AI Agent for discovering and extracting legal document metadata
    Uses LangGraph for orchestration and Gemini for intelligent decision-making
    """
    
    def __init__(self, google_api_key: str = None):
        """
        Initialize the Metadata Discovery Agent
        
        Args:
            google_api_key: Google API key for Gemini (optional, uses config if not provided)
        """
        api_key = google_api_key or config.google_api_key
        
        if not api_key or api_key == "your_google_api_key_here":
            raise ValueError(
                "Google API key not configured. Please set GOOGLE_API_KEY in .env file"
            )
        
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=api_key,
            temperature=0.1,
            max_retries=3
        )
        
        # Build the graph
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the graph
        workflow = StateGraph(MetadataDiscoveryState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("search_documents", self._search_documents_node)
        workflow.add_node("analyze_results", self._analyze_results_node)
        workflow.add_node("extract_metadata", self._extract_metadata_node)
        workflow.add_node("filter_relevant", self._filter_relevant_node)
        workflow.add_node("save_metadata", self._save_metadata_node)
        
        # Define the flow
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "search_documents")
        workflow.add_edge("search_documents", "analyze_results")
        workflow.add_edge("analyze_results", "extract_metadata")
        workflow.add_edge("extract_metadata", "filter_relevant")
        workflow.add_edge("filter_relevant", "save_metadata")
        workflow.add_edge("save_metadata", END)
        
        return workflow.compile()
    
    def _initialize_node(self, state: MetadataDiscoveryState) -> MetadataDiscoveryState:
        """Initialize the agent state"""
        logger.info("=== INITIALIZING METADATA DISCOVERY AGENT ===")
        
        state["current_step"] = "initialize"
        state["raw_documents"] = []
        state["filtered_documents"] = []
        state["metadata_list"] = []
        state["total_discovered"] = 0
        state["total_relevant"] = 0
        state["error"] = ""
        
        if "messages" not in state:
            state["messages"] = []
        
        # Get keywords from config if not provided
        if not state.get("keywords"):
            state["keywords"] = config.get_all_keywords()[:10]  # Use top 10 keywords
        
        # Set default source
        if not state.get("source"):
            state["source"] = "vanban_chinhphu"
        
        # Set default max documents
        if not state.get("max_documents"):
            state["max_documents"] = 50
        
        logger.info(f"Keywords: {state['keywords'][:5]}... ({len(state['keywords'])} total)")
        logger.info(f"Source: {state['source']}")
        logger.info(f"Max documents: {state['max_documents']}")
        
        return state
    
    def _search_documents_node(self, state: MetadataDiscoveryState) -> MetadataDiscoveryState:
        """Search for documents from the source"""
        logger.info("=== SEARCHING FOR DOCUMENTS ===")
        
        state["current_step"] = "search_documents"
        
        try:
            # Use the search tool
            search_result = search_vanban_chinhphu.invoke({
                "keywords": state["keywords"],
                "max_pages": 5
            })
            
            if search_result["success"]:
                state["raw_documents"] = search_result["documents"]
                state["total_discovered"] = search_result["total_found"]
                logger.info(f"Found {state['total_discovered']} documents")
            else:
                state["error"] = f"Search failed: {search_result['error']}"
                logger.error(state["error"])
                
        except Exception as e:
            state["error"] = f"Error during search: {str(e)}"
            logger.error(state["error"])
        
        return state
    
    def _analyze_results_node(self, state: MetadataDiscoveryState) -> MetadataDiscoveryState:
        """Use Gemini to analyze search results and plan next steps"""
        logger.info("=== ANALYZING SEARCH RESULTS WITH GEMINI ===")
        
        state["current_step"] = "analyze_results"
        
        try:
            # Prepare summary for Gemini
            summary = {
                "total_found": state["total_discovered"],
                "sample_titles": [doc.get("title", "")[:100] for doc in state["raw_documents"][:5]],
                "keywords_used": state["keywords"][:10]
            }
            
            system_prompt = """Bạn là chuyên gia phân tích văn bản pháp luật Việt Nam về công nghệ số.
            
Nhiệm vụ: Phân tích kết quả tìm kiếm và đánh giá mức độ liên quan của các văn bản với chủ đề:
"Công nghệ số, chuyển đổi số, chính sách thúc đẩy công nghệ tại Việt Nam"

Hãy đánh giá:
1. Các văn bản có phù hợp với chủ đề không?
2. Có cần điều chỉnh từ khóa tìm kiếm không?
3. Nên ưu tiên loại văn bản nào (Luật, Nghị định, Quyết định...)?

Trả lời ngắn gọn bằng tiếng Việt, tập trung vào khuyến nghị cụ thể."""
            
            user_prompt = f"""Kết quả tìm kiếm:
- Tổng số văn bản: {summary['total_found']}
- Từ khóa sử dụng: {', '.join(summary['keywords_used'])}
- Mẫu tiêu đề:
{chr(10).join(f"  + {title}" for title in summary['sample_titles'])}

Hãy phân tích và đưa ra đánh giá."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = self.llm.invoke(messages)
            analysis = response.content
            
            logger.info(f"Gemini Analysis:\n{analysis}")
            
            state["messages"].append({
                "role": "assistant",
                "content": analysis,
                "step": "analyze_results"
            })
            
        except Exception as e:
            logger.warning(f"Could not get Gemini analysis: {str(e)}")
            state["messages"].append({
                "role": "system",
                "content": f"Analysis skipped: {str(e)}",
                "step": "analyze_results"
            })
        
        return state
    
    def _extract_metadata_node(self, state: MetadataDiscoveryState) -> MetadataDiscoveryState:
        """Extract metadata from raw documents"""
        logger.info("=== EXTRACTING METADATA ===")
        
        state["current_step"] = "extract_metadata"
        
        metadata_list = []
        
        for idx, doc in enumerate(state["raw_documents"][:state["max_documents"]]):
            try:
                logger.info(f"Processing document {idx+1}/{len(state['raw_documents'][:state['max_documents']])}")
                
                result = extract_document_metadata.invoke({"raw_document": doc})
                
                if result["success"] and result["metadata"]:
                    metadata_list.append(result["metadata"])
                else:
                    logger.warning(f"Failed to extract metadata: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error extracting metadata for document {idx+1}: {str(e)}")
                continue
        
        state["metadata_list"] = metadata_list
        logger.info(f"Extracted metadata for {len(metadata_list)} documents")
        
        return state
    
    def _filter_relevant_node(self, state: MetadataDiscoveryState) -> MetadataDiscoveryState:
        """Filter documents based on keyword relevance"""
        logger.info("=== FILTERING RELEVANT DOCUMENTS ===")
        
        state["current_step"] = "filter_relevant"
        
        try:
            # Filter based on keywords in metadata
            relevant_docs = []
            
            for metadata in state["metadata_list"]:
                # Check if has enough keywords or specific document types
                if len(metadata.get("keywords", [])) >= 2:
                    relevant_docs.append(metadata)
                elif metadata.get("doc_type") in ["Luật", "Nghị định", "Quyết định"]:
                    # Keep important document types even with fewer keywords
                    relevant_docs.append(metadata)
            
            state["filtered_documents"] = relevant_docs
            state["total_relevant"] = len(relevant_docs)
            
            logger.info(f"Filtered to {state['total_relevant']} relevant documents out of {len(state['metadata_list'])}")
            
        except Exception as e:
            state["error"] = f"Error during filtering: {str(e)}"
            logger.error(state["error"])
            state["filtered_documents"] = state["metadata_list"]  # Use all if filtering fails
            state["total_relevant"] = len(state["metadata_list"])
        
        return state
    
    def _save_metadata_node(self, state: MetadataDiscoveryState) -> MetadataDiscoveryState:
        """Save metadata to file"""
        logger.info("=== SAVING METADATA ===")
        
        state["current_step"] = "save_metadata"
        
        try:
            # Create metadata directory if not exists
            config.metadata_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metadata_{state['source']}_{timestamp}.json"
            filepath = config.metadata_dir / filename
            
            # Prepare output data
            output_data = {
                "metadata": {
                    "source": state["source"],
                    "keywords": state["keywords"],
                    "crawl_timestamp": datetime.now().isoformat(),
                    "total_discovered": state["total_discovered"],
                    "total_relevant": state["total_relevant"]
                },
                "documents": state["filtered_documents"]
            }
            
            # Save to JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            state["saved_metadata_path"] = str(filepath)
            logger.info(f"Metadata saved to: {filepath}")
            
            # Also save as CSV for easy viewing
            self._save_as_csv(state["filtered_documents"], filepath.with_suffix('.csv'))
            
        except Exception as e:
            state["error"] = f"Error saving metadata: {str(e)}"
            logger.error(state["error"])
        
        return state
    
    def _save_as_csv(self, documents: List[Dict[str, Any]], filepath: Path):
        """Save metadata as CSV"""
        try:
            import pandas as pd
            
            # Flatten the data for CSV
            csv_data = []
            for doc in documents:
                csv_data.append({
                    "doc_id": doc.get("doc_id", ""),
                    "title": doc.get("title", ""),
                    "doc_type": doc.get("doc_type", ""),
                    "doc_number": doc.get("doc_number", ""),
                    "issuer": doc.get("issuer", ""),
                    "issue_date": doc.get("issue_date", ""),
                    "status": doc.get("status", ""),
                    "url": doc.get("url", ""),
                    "keywords": ", ".join(doc.get("keywords", [])[:10]),
                    "source": doc.get("source", "")
                })
            
            df = pd.DataFrame(csv_data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            logger.info(f"CSV saved to: {filepath}")
            
        except Exception as e:
            logger.warning(f"Could not save CSV: {str(e)}")
    
    def run(self, keywords: List[str] = None, max_documents: int = 50) -> Dict[str, Any]:
        """
        Run the metadata discovery agent
        
        Args:
            keywords: List of keywords to search (optional, uses config if not provided)
            max_documents: Maximum number of documents to process
            
        Returns:
            Dictionary with results
        """
        logger.info("=" * 60)
        logger.info("STARTING METADATA DISCOVERY AGENT")
        logger.info("=" * 60)
        
        # Initialize state
        initial_state = {
            "keywords": keywords or config.get_all_keywords()[:10],
            "source": "vanban_chinhphu",
            "max_documents": max_documents,
            "messages": []
        }
        
        # Run the graph
        try:
            final_state = self.graph.invoke(initial_state)
            
            logger.info("=" * 60)
            logger.info("METADATA DISCOVERY COMPLETED")
            logger.info(f"Total discovered: {final_state['total_discovered']}")
            logger.info(f"Total relevant: {final_state['total_relevant']}")
            logger.info(f"Saved to: {final_state.get('saved_metadata_path', 'N/A')}")
            logger.info("=" * 60)
            
            return {
                "success": True,
                "total_discovered": final_state["total_discovered"],
                "total_relevant": final_state["total_relevant"],
                "metadata_path": final_state.get("saved_metadata_path", ""),
                "error": final_state.get("error", "")
            }
            
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "total_discovered": 0,
                "total_relevant": 0,
                "metadata_path": ""
            }
