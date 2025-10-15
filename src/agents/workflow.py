"""
LangGraph Workflow for Vietnamese Legal Crawler AI Agent
"""
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents.state import AgentState, WorkflowStep, create_initial_state
from src.agents.nodes import PlannerNode, CrawlerNode, AnalyzerNode, SummarizerNode
from src.utils.logger import log


class LegalCrawlerWorkflow:
    """
    Main workflow for Legal Document Crawler AI Agent
    """
    
    def __init__(self):
        """Initialize workflow"""
        self.planner = PlannerNode()
        self.crawler = CrawlerNode()
        self.analyzer = AnalyzerNode()
        self.summarizer = SummarizerNode()
        
        # Build graph
        self.graph = self._build_graph()
        self.app = self.graph.compile(checkpointer=MemorySaver())
        
        log.info("Legal Crawler Workflow initialized")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the workflow graph
        
        Returns:
            Compiled StateGraph
        """
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("planner", self.planner)
        workflow.add_node("crawler", self.crawler)
        workflow.add_node("analyzer", self.analyzer)
        workflow.add_node("summarizer", self.summarizer)
        
        # Define edges
        workflow.set_entry_point("planner")
        
        # Planner -> Crawler
        workflow.add_edge("planner", "crawler")
        
        # Crawler -> Analyzer
        workflow.add_edge("crawler", "analyzer")
        
        # Analyzer -> Summarizer
        workflow.add_edge("analyzer", "summarizer")
        
        # Summarizer -> END
        workflow.add_edge("summarizer", END)
        
        log.info("Workflow graph built with nodes: planner -> crawler -> analyzer -> summarizer")
        
        return workflow
    
    async def run(
        self,
        user_query: str,
        target_websites: list = None,
        max_iterations: int = 1
    ) -> AgentState:
        """
        Run the workflow
        
        Args:
            user_query: User's search query
            target_websites: Optional list of specific websites
            max_iterations: Maximum iterations (default: 1)
            
        Returns:
            Final AgentState
        """
        log.info("="*60)
        log.info("Starting Legal Crawler AI Agent Workflow")
        log.info("="*60)
        log.info(f"Query: {user_query}")
        
        # Create initial state
        initial_state = create_initial_state(
            user_query=user_query,
            target_websites=target_websites,
            max_iterations=max_iterations
        )
        
        # Run workflow
        try:
            config = {"configurable": {"thread_id": "1"}}
            
            final_state = None
            async for state in self.app.astream(initial_state, config):
                # Log progress
                for node_name, node_state in state.items():
                    if node_state:
                        current_step = node_state.get('current_step', 'unknown')
                        log.info(f"Node '{node_name}' completed. Current step: {current_step}")
                        final_state = node_state
            
            log.info("="*60)
            log.info("Workflow completed successfully")
            log.info("="*60)
            
            return final_state
            
        except Exception as e:
            log.error(f"Workflow failed: {e}")
            raise


class SimpleWorkflow:
    """
    Simplified workflow for testing
    """
    
    def __init__(self):
        self.planner = PlannerNode()
        self.crawler = CrawlerNode()
        self.analyzer = AnalyzerNode()
        self.summarizer = SummarizerNode()
    
    async def run(self, user_query: str) -> dict:
        """
        Run simplified workflow without LangGraph
        
        Args:
            user_query: User query
            
        Returns:
            Results dictionary
        """
        log.info("Running simplified workflow")
        
        # Create initial state
        state = create_initial_state(user_query)
        
        # Step 1: Planning
        log.info("\n--- Step 1: Planning ---")
        plan_result = await self.planner(state)
        state.update(plan_result)
        
        # Step 2: Crawling
        log.info("\n--- Step 2: Crawling ---")
        crawl_result = await self.crawler(state)
        state.update(crawl_result)
        
        # Step 3: Analysis
        log.info("\n--- Step 3: Analysis ---")
        analysis_result = await self.analyzer(state)
        state.update(analysis_result)
        
        # Step 4: Summarization
        log.info("\n--- Step 4: Summarization ---")
        summary_result = await self.summarizer(state)
        state.update(summary_result)
        
        return state


# Convenience function
async def run_legal_crawler_agent(
    user_query: str,
    simple_mode: bool = False
) -> dict:
    """
    Convenience function to run the agent
    
    Args:
        user_query: User's search query
        simple_mode: Use simplified workflow without LangGraph
        
    Returns:
        Final state with results
    """
    if simple_mode:
        workflow = SimpleWorkflow()
    else:
        workflow = LegalCrawlerWorkflow()
    
    result = await workflow.run(user_query)
    return result
