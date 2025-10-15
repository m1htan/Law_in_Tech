"""
Test script for Vietnamese Legal Crawler AI Agent
"""
import asyncio
from src.config import Config
from src.agents.workflow import SimpleWorkflow, LegalCrawlerWorkflow
from src.agents.llm_config import test_llm_connection
from src.utils.logger import log


async def test_llm_only():
    """Test LLM connection first"""
    print("\n" + "="*60)
    print("TEST 1: Gemini LLM Connection")
    print("="*60)
    
    try:
        Config.validate(require_api_key=True)
        print("✓ API Key configured")
        
        success = test_llm_connection()
        if success:
            print("✓ LLM connection successful")
            return True
        else:
            print("✗ LLM connection failed")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


async def test_simple_workflow():
    """Test simplified workflow"""
    print("\n" + "="*60)
    print("TEST 2: Simple Workflow (Without LangGraph)")
    print("="*60)
    
    # Test query
    user_query = "Tìm các văn bản pháp luật về chuyển đổi số và công nghệ thông tin từ năm 2022"
    
    print(f"\nUser Query: {user_query}")
    print("\nStarting workflow...\n")
    
    try:
        workflow = SimpleWorkflow()
        result = await workflow.run(user_query)
        
        print("\n" + "="*60)
        print("WORKFLOW RESULTS")
        print("="*60)
        
        # Display statistics
        if result.get('statistics'):
            print("\n📊 STATISTICS:")
            for key, value in result['statistics'].items():
                print(f"  - {key}: {value}")
        
        # Display relevant documents
        relevant_docs = result.get('relevant_documents', [])
        print(f"\n📄 RELEVANT DOCUMENTS: {len(relevant_docs)}")
        for idx, doc_analysis in enumerate(relevant_docs, 1):
            doc = doc_analysis['document']
            score = doc_analysis['relevance_score']
            print(f"\n  {idx}. {doc.get('source_name', 'Unknown')}")
            print(f"     URL: {doc.get('url', '')}")
            print(f"     Relevance Score: {score}/10")
        
        # Display final report
        if result.get('final_report'):
            print("\n" + "="*60)
            print("📋 FINAL REPORT")
            print("="*60)
            print(result['final_report'])
        
        # Display failed crawls
        failed = result.get('failed_crawls', [])
        if failed:
            print(f"\n⚠️ FAILED CRAWLS: {len(failed)}")
            for fail in failed:
                print(f"  - {fail.get('website', 'Unknown')}: {fail.get('reason', 'Unknown')}")
        
        print("\n" + "="*60)
        print("✅ Workflow completed successfully!")
        print("="*60)
        
        return result
        
    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_full_workflow():
    """Test full LangGraph workflow"""
    print("\n" + "="*60)
    print("TEST 3: Full LangGraph Workflow")
    print("="*60)
    
    user_query = "Tìm các văn bản về trí tuệ nhân tạo và dữ liệu lớn"
    
    print(f"\nUser Query: {user_query}")
    print("\nStarting LangGraph workflow...\n")
    
    try:
        workflow = LegalCrawlerWorkflow()
        result = await workflow.run(user_query)
        
        print("\n" + "="*60)
        print("✅ LangGraph workflow completed!")
        print("="*60)
        
        if result.get('final_report'):
            print("\n" + result['final_report'])
        
        return result
        
    except Exception as e:
        print(f"\n✗ LangGraph workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def quick_test():
    """Quick test with minimal crawling"""
    print("\n" + "="*60)
    print("QUICK TEST: AI Agent với 2 trang web")
    print("="*60)
    
    user_query = "Văn bản về công nghệ thông tin"
    
    try:
        # Only test with 2 verified sites
        from src.agents.state import create_initial_state
        
        # Create workflow
        workflow = SimpleWorkflow()
        
        # Modify state to use only 2 websites
        state = create_initial_state(user_query)
        state['target_websites'] = [
            'https://chinhphu.vn',
            'https://mst.gov.vn'
        ]
        
        # Run manually
        print("\n1. Planning...")
        plan_result = await workflow.planner(state)
        state.update(plan_result)
        print(f"   Selected {len(state.get('selected_websites', []))} websites")
        
        print("\n2. Crawling...")
        # Limit to 2 sites
        state['selected_websites'] = state['selected_websites'][:2]
        crawl_result = await workflow.crawler(state)
        state.update(crawl_result)
        print(f"   Crawled {len(state.get('crawled_documents', []))} documents")
        
        print("\n3. Analyzing...")
        analysis_result = await workflow.analyzer(state)
        state.update(analysis_result)
        print(f"   Found {len(state.get('relevant_documents', []))} relevant documents")
        
        print("\n4. Summarizing...")
        summary_result = await workflow.summarizer(state)
        state.update(summary_result)
        
        print("\n" + "="*60)
        print("RESULTS")
        print("="*60)
        
        if state.get('statistics'):
            print("\nStatistics:")
            for k, v in state['statistics'].items():
                print(f"  {k}: {v}")
        
        if state.get('final_report'):
            print("\nReport:")
            print(state['final_report'][:500] + "...")
        
        print("\n✅ Quick test completed!")
        
        return state
        
    except Exception as e:
        print(f"\n✗ Quick test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Vietnamese Legal Crawler AI Agent - Test Suite")
    print("="*60)
    
    # Test 1: LLM Connection
    llm_ok = await test_llm_only()
    if not llm_ok:
        print("\n❌ LLM connection failed. Please check your API key.")
        return
    
    print("\n\n")
    await asyncio.sleep(2)
    
    # Test 2: Quick test
    print("\nRunning quick test...")
    quick_result = await quick_test()
    
    if not quick_result:
        print("\n❌ Quick test failed")
        return
    
    print("\n\n")
    print("="*60)
    print("Do you want to run full test? (takes longer)")
    print("="*60)
    print("\nSkipping full test for now. Quick test passed!")
    print("\nTo run full test, use: test_simple_workflow() or test_full_workflow()")


if __name__ == "__main__":
    asyncio.run(main())
