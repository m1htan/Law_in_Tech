"""
State management for LangGraph AI Agent
"""
from typing import TypedDict, List, Dict, Optional, Annotated
from datetime import datetime
import operator


class AgentState(TypedDict):
    """
    State for Vietnamese Legal Crawler AI Agent
    
    This state is passed between nodes in the LangGraph workflow
    """
    
    # User input and configuration
    user_query: str
    search_keywords: List[str]
    target_websites: List[str]
    
    # Planning phase
    crawl_plan: Optional[Dict]
    selected_websites: List[Dict]
    
    # Crawling phase
    crawled_documents: Annotated[List[Dict], operator.add]  # Accumulate documents
    crawl_results: List[Dict]
    failed_crawls: Annotated[List[Dict], operator.add]  # Accumulate failures
    
    # Analysis phase
    analyzed_documents: Annotated[List[Dict], operator.add]  # Accumulate analyses
    relevant_documents: List[Dict]
    document_summaries: List[str]
    
    # Opinion/Comment extraction
    user_opinions: Annotated[List[Dict], operator.add]  # Accumulate opinions
    opinion_summary: Optional[str]
    
    # Final output
    final_report: Optional[str]
    statistics: Optional[Dict]
    
    # Workflow control
    current_step: str
    iteration: int
    max_iterations: int
    should_continue: bool
    error_message: Optional[str]
    
    # Metadata
    started_at: str
    completed_at: Optional[str]
    messages: Annotated[List[Dict], operator.add]  # Chat history


def create_initial_state(
    user_query: str,
    target_websites: Optional[List[str]] = None,
    max_iterations: int = 5
) -> AgentState:
    """
    Create initial state for the agent
    
    Args:
        user_query: User's search query
        target_websites: Optional list of specific websites to crawl
        max_iterations: Maximum iterations for the workflow
        
    Returns:
        Initial AgentState
    """
    from src.config import Config
    
    if target_websites is None:
        # Use verified websites from config
        target_websites = [w['url'] for w in Config.get_verified_websites()]
    
    return AgentState(
        # User input
        user_query=user_query,
        search_keywords=[],
        target_websites=target_websites,
        
        # Planning
        crawl_plan=None,
        selected_websites=[],
        
        # Crawling
        crawled_documents=[],
        crawl_results=[],
        failed_crawls=[],
        
        # Analysis
        analyzed_documents=[],
        relevant_documents=[],
        document_summaries=[],
        
        # Opinions
        user_opinions=[],
        opinion_summary=None,
        
        # Output
        final_report=None,
        statistics=None,
        
        # Control
        current_step="init",
        iteration=0,
        max_iterations=max_iterations,
        should_continue=True,
        error_message=None,
        
        # Metadata
        started_at=datetime.now().isoformat(),
        completed_at=None,
        messages=[]
    )


class WorkflowStep:
    """Constants for workflow steps"""
    INIT = "init"
    PLANNING = "planning"
    CRAWLING = "crawling"
    ANALYSIS = "analysis"
    OPINION_EXTRACTION = "opinion_extraction"
    SUMMARIZATION = "summarization"
    COMPLETED = "completed"
    ERROR = "error"
