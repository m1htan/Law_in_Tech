"""
Agent nodes for LangGraph workflow
"""
import asyncio
from typing import Dict, List
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage

from src.agents.state import AgentState, WorkflowStep
from src.agents.llm_config import LLMConfig
from src.crawlers.legal_website_crawler import LegalWebsiteCrawler
from src.config import Config
from src.utils.logger import log


class PlannerNode:
    """
    Planner Agent Node - Lập kế hoạch crawl
    """
    
    def __init__(self):
        self.llm = LLMConfig.get_gemini_llm(temperature=0.3)
        self.prompt = LLMConfig.create_planner_prompt()
    
    async def __call__(self, state: AgentState) -> Dict:
        """
        Execute planner node
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state dict
        """
        log.info("=== PLANNER NODE ===")
        log.info(f"User query: {state['user_query']}")
        
        try:
            # Prepare context
            available_websites = Config.get_verified_websites()
            website_info = "\n".join([
                f"- {w['name']} ({w['url']}) - {w['type']}"
                for w in available_websites
            ])
            
            # Create planning prompt
            planning_input = f"""
Người dùng yêu cầu: "{state['user_query']}"

Các trang web có sẵn:
{website_info}

Hãy:
1. Phân tích yêu cầu và xác định từ khóa tìm kiếm
2. Chọn 3-5 trang web phù hợp nhất
3. Đề xuất chiến lược crawl

Trả lời theo format:
TỪ KHÓA: [danh sách từ khóa, cách nhau bởi dấu ;]
TRANG WEB: [danh sách tên trang, cách nhau bởi dấu ;]
LÝ DO: [giải thích ngắn gọn]
"""
            
            # Get LLM response
            messages = state.get('messages', [])
            messages.append(HumanMessage(content=planning_input))
            
            chain = self.prompt | self.llm
            response = await asyncio.to_thread(
                chain.invoke,
                {"input": planning_input, "messages": messages}
            )
            
            # Parse response
            plan_text = response.content
            log.info(f"Plan generated:\n{plan_text}")
            
            # Extract keywords
            keywords = self._extract_keywords(plan_text)
            log.info(f"Extracted keywords: {keywords}")
            
            # Select websites
            selected_sites = self._select_websites(plan_text, available_websites)
            log.info(f"Selected {len(selected_sites)} websites")
            
            # Update state
            return {
                "current_step": WorkflowStep.CRAWLING,
                "search_keywords": keywords,
                "selected_websites": selected_sites,
                "crawl_plan": {
                    "plan_text": plan_text,
                    "created_at": datetime.now().isoformat()
                },
                "messages": [AIMessage(content=plan_text)]
            }
            
        except Exception as e:
            log.error(f"Planner node failed: {e}")
            return {
                "current_step": WorkflowStep.ERROR,
                "error_message": f"Planning failed: {str(e)}",
                "should_continue": False
            }
    
    def _extract_keywords(self, plan_text: str) -> List[str]:
        """Extract keywords from plan text"""
        keywords = []
        
        # Look for keywords section
        for line in plan_text.split('\n'):
            if 'TỪ KHÓA' in line or 'KEYWORDS' in line.upper():
                # Extract after colon
                parts = line.split(':', 1)
                if len(parts) > 1:
                    kw_text = parts[1].strip()
                    # Split by semicolon or comma
                    keywords = [k.strip() for k in kw_text.replace(';', ',').split(',') if k.strip()]
                    break
        
        # Fallback: use tech keywords from config
        if not keywords:
            keywords = Config.TECH_KEYWORDS[:5]
        
        return keywords
    
    def _select_websites(self, plan_text: str, available_websites: List[Dict]) -> List[Dict]:
        """Select websites based on plan"""
        selected = []
        
        # Look for website mentions in plan
        plan_lower = plan_text.lower()
        
        for website in available_websites:
            name_lower = website['name'].lower()
            url_lower = website['url'].lower()
            
            # Check if website is mentioned
            if name_lower in plan_lower or url_lower in plan_lower:
                selected.append(website)
        
        # If none selected, use high priority ones
        if not selected:
            selected = Config.get_high_priority_websites()[:3]
        
        return selected


class CrawlerNode:
    """
    Crawler Agent Node - Thực hiện crawl
    """
    
    async def __call__(self, state: AgentState) -> Dict:
        """
        Execute crawler node
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state dict
        """
        log.info("=== CRAWLER NODE ===")
        
        selected_websites = state.get('selected_websites', [])
        log.info(f"Crawling {len(selected_websites)} websites")
        
        crawled_documents = []
        failed_crawls = []
        
        for idx, website_config in enumerate(selected_websites, 1):
            try:
                log.info(f"[{idx}/{len(selected_websites)}] Crawling: {website_config['name']}")
                
                # Create crawler
                crawler = LegalWebsiteCrawler(website_config)
                
                # Crawl homepage
                result = await crawler.crawl_url(
                    website_config['url'],
                    extract_pdfs=True,
                    retry=2
                )
                
                if result:
                    # Add source info
                    result['source_name'] = website_config['name']
                    result['source_type'] = website_config['type']
                    
                    crawled_documents.append(result)
                    log.info(f"✓ Successfully crawled: {website_config['name']}")
                else:
                    failed_crawls.append({
                        'website': website_config['name'],
                        'url': website_config['url'],
                        'reason': 'No data returned'
                    })
                    log.warning(f"✗ Failed to crawl: {website_config['name']}")
                
                # Delay between crawls
                if idx < len(selected_websites):
                    await asyncio.sleep(Config.REQUEST_DELAY)
                    
            except Exception as e:
                log.error(f"Error crawling {website_config['name']}: {e}")
                failed_crawls.append({
                    'website': website_config['name'],
                    'url': website_config['url'],
                    'reason': str(e)
                })
        
        log.info(f"Crawling complete: {len(crawled_documents)} successful, {len(failed_crawls)} failed")
        
        # Update state
        return {
            "current_step": WorkflowStep.ANALYSIS,
            "crawled_documents": crawled_documents,
            "failed_crawls": failed_crawls,
            "iteration": state.get('iteration', 0) + 1
        }


class AnalyzerNode:
    """
    Analyzer Agent Node - Phân tích văn bản
    """
    
    def __init__(self):
        self.llm = LLMConfig.get_gemini_llm(temperature=0.2)
        self.prompt = LLMConfig.create_analyzer_prompt()
    
    async def __call__(self, state: AgentState) -> Dict:
        """
        Execute analyzer node
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state dict
        """
        log.info("=== ANALYZER NODE ===")
        
        crawled_documents = state.get('crawled_documents', [])
        log.info(f"Analyzing {len(crawled_documents)} documents")
        
        analyzed_documents = []
        relevant_documents = []
        
        for idx, doc in enumerate(crawled_documents, 1):
            try:
                log.info(f"[{idx}/{len(crawled_documents)}] Analyzing: {doc.get('source_name', 'Unknown')}")
                
                # Prepare content for analysis
                content = doc.get('markdown', '')[:3000]  # First 3000 chars
                title = doc.get('metadata', {}).get('title', '')
                
                # Build analysis request
                analysis_request = f"""
Tên trang: {doc.get('source_name')}
URL: {doc.get('url')}
Tiêu đề: {title}

Nội dung (preview):
{content}

Hãy phân tích và cho biết:
1. Đây có phải là trang về văn bản luật không?
2. Có liên quan đến công nghệ/chuyển đổi số không?
3. Mức độ phù hợp với yêu cầu (0-10)
4. Tóm tắt ngắn gọn (1-2 câu)
"""
                
                # Get LLM analysis
                messages = []
                chain = self.prompt | self.llm
                response = await asyncio.to_thread(
                    chain.invoke,
                    {"document_content": analysis_request, "messages": messages}
                )
                
                analysis_text = response.content
                
                # Parse relevance score
                relevance_score = self._extract_relevance_score(analysis_text)
                
                # Create analysis result
                analysis = {
                    'document': doc,
                    'analysis': analysis_text,
                    'relevance_score': relevance_score,
                    'analyzed_at': datetime.now().isoformat()
                }
                
                analyzed_documents.append(analysis)
                
                # Add to relevant if score >= 5
                if relevance_score >= 5:
                    relevant_documents.append(analysis)
                    log.info(f"✓ Relevant document (score: {relevance_score})")
                else:
                    log.info(f"✗ Not relevant (score: {relevance_score})")
                
            except Exception as e:
                log.error(f"Error analyzing document: {e}")
        
        log.info(f"Analysis complete: {len(relevant_documents)}/{len(crawled_documents)} relevant")
        
        # Update state
        return {
            "current_step": WorkflowStep.SUMMARIZATION,
            "analyzed_documents": analyzed_documents,
            "relevant_documents": relevant_documents
        }
    
    def _extract_relevance_score(self, analysis_text: str) -> int:
        """Extract relevance score from analysis"""
        import re
        
        # Look for patterns like "8/10", "Mức độ: 7", etc.
        patterns = [
            r'(\d+)/10',
            r'mức độ[:\s]+(\d+)',
            r'điểm[:\s]+(\d+)',
            r'score[:\s]+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, analysis_text, re.IGNORECASE)
            if match:
                score = int(match.group(1))
                return min(max(score, 0), 10)  # Clamp to 0-10
        
        # Default: if marked as relevant, give 7, else 3
        if 'có liên quan' in analysis_text.lower() or 'relevant' in analysis_text.lower():
            return 7
        else:
            return 3


class SummarizerNode:
    """
    Summarizer Agent Node - Tổng hợp kết quả
    """
    
    def __init__(self):
        self.llm = LLMConfig.get_gemini_llm(temperature=0.4)
        self.prompt = LLMConfig.create_summarizer_prompt()
    
    async def __call__(self, state: AgentState) -> Dict:
        """
        Execute summarizer node
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state dict
        """
        log.info("=== SUMMARIZER NODE ===")
        
        relevant_docs = state.get('relevant_documents', [])
        crawled_docs = state.get('crawled_documents', [])
        failed_crawls = state.get('failed_crawls', [])
        
        log.info(f"Creating summary from {len(relevant_docs)} relevant documents")
        
        try:
            # Prepare summary data
            summary_input = self._prepare_summary_input(
                state['user_query'],
                relevant_docs,
                crawled_docs,
                failed_crawls
            )
            
            # Generate summary
            messages = []
            chain = self.prompt | self.llm
            response = await asyncio.to_thread(
                chain.invoke,
                {"analysis_results": summary_input, "messages": messages}
            )
            
            final_report = response.content
            
            # Create statistics
            statistics = {
                'total_websites_crawled': len(crawled_docs),
                'successful_crawls': len(crawled_docs),
                'failed_crawls': len(failed_crawls),
                'relevant_documents': len(relevant_docs),
                'relevance_rate': f"{len(relevant_docs)/max(len(crawled_docs), 1)*100:.1f}%"
            }
            
            log.info("Summary generated successfully")
            
            return {
                "current_step": WorkflowStep.COMPLETED,
                "final_report": final_report,
                "statistics": statistics,
                "should_continue": False,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            log.error(f"Summarizer node failed: {e}")
            return {
                "current_step": WorkflowStep.ERROR,
                "error_message": f"Summarization failed: {str(e)}",
                "should_continue": False
            }
    
    def _prepare_summary_input(
        self,
        user_query: str,
        relevant_docs: List[Dict],
        all_docs: List[Dict],
        failed: List[Dict]
    ) -> str:
        """Prepare input for summarizer"""
        
        # Build document list
        doc_summaries = []
        for idx, doc_analysis in enumerate(relevant_docs, 1):
            doc = doc_analysis['document']
            analysis = doc_analysis['analysis']
            score = doc_analysis['relevance_score']
            
            summary = f"""
{idx}. {doc.get('source_name', 'Unknown')}
   URL: {doc.get('url', '')}
   Relevance: {score}/10
   Analysis: {analysis[:200]}...
"""
            doc_summaries.append(summary)
        
        # Build summary input
        summary_input = f"""
YÊU CẦU: {user_query}

THỐNG KÊ:
- Tổng số trang crawl: {len(all_docs)}
- Văn bản liên quan: {len(relevant_docs)}
- Crawl thất bại: {len(failed)}

CÁC VĂN BẢN LIÊN QUAN:
{''.join(doc_summaries) if doc_summaries else 'Không tìm thấy văn bản liên quan'}
"""
        
        return summary_input
