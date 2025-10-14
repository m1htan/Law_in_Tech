"""
LLM Configuration for Vietnamese Legal Crawler AI Agent
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from src.config import Config
from src.utils.logger import log


class LLMConfig:
    """LLM configuration and setup"""
    
    @staticmethod
    def get_gemini_llm(
        model: str = "gemini-1.5-flash",
        temperature: float = 0.3,
        **kwargs
    ) -> ChatGoogleGenerativeAI:
        """
        Get configured Gemini LLM
        
        Args:
            model: Gemini model name
            temperature: Temperature for generation (0-1)
            **kwargs: Additional parameters
            
        Returns:
            Configured ChatGoogleGenerativeAI instance
        """
        if not Config.GOOGLE_API_KEY or Config.GOOGLE_API_KEY == "your_google_api_key_here":
            raise ValueError(
                "GOOGLE_API_KEY not configured. Please set it in .env file"
            )
        
        log.info(f"Initializing Gemini LLM: {model}")
        
        llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=Config.GOOGLE_API_KEY,
            convert_system_message_to_human=True,  # Gemini compatibility
            **kwargs
        )
        
        return llm
    
    @staticmethod
    def create_planner_prompt() -> ChatPromptTemplate:
        """
        Create prompt template for Planner Agent
        
        Returns:
            ChatPromptTemplate for planning
        """
        system_message = """Bạn là một AI Agent chuyên gia về pháp luật Việt Nam, 
được giao nhiệm vụ lập kế hoạch thu thập dữ liệu về các văn bản pháp luật.

NHIỆM VỤ:
- Phân tích yêu cầu tìm kiếm của người dùng
- Quyết định nên crawl những trang web nào
- Ưu tiên các trang có khả năng chứa thông tin liên quan cao
- Đề xuất từ khóa tìm kiếm phù hợp

CHUYÊN MÔN:
- Văn bản luật Việt Nam: Nghị quyết, Nghị định, Thông tư, Quyết định, Dự thảo
- Các chủ đề: Công nghệ, Chuyển đổi số, AI, An ninh mạng, Dữ liệu
- Các nguồn tin uy tín: Chính phủ, Bộ ngành, Quốc hội

TRẢ LỜI BẰNG TIẾNG VIỆT."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}")
        ])
        
        return prompt
    
    @staticmethod
    def create_analyzer_prompt() -> ChatPromptTemplate:
        """
        Create prompt template for Analyzer Agent
        
        Returns:
            ChatPromptTemplate for analysis
        """
        system_message = """Bạn là một AI Agent chuyên gia phân tích văn bản pháp luật Việt Nam.

NHIỆM VỤ:
- Phân tích nội dung văn bản luật đã crawl được
- Tóm tắt nội dung chính
- Xác định chủ đề và lĩnh vực
- Đánh giá mức độ liên quan với yêu cầu tìm kiếm
- Trích xuất thông tin quan trọng

CẤU TRÚC PHÂN TÍCH:
1. Tên văn bản & Loại văn bản
2. Ngày ban hành
3. Tóm tắt nội dung (2-3 câu)
4. Chủ đề chính
5. Từ khóa liên quan
6. Mức độ phù hợp (0-10)

TRẢ LỜI BẰNG TIẾNG VIỆT."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "Phân tích văn bản sau:\n\n{document_content}")
        ])
        
        return prompt
    
    @staticmethod
    def create_summarizer_prompt() -> ChatPromptTemplate:
        """
        Create prompt template for Summarizer Agent
        
        Returns:
            ChatPromptTemplate for summarization
        """
        system_message = """Bạn là một AI Agent chuyên tóm tắt văn bản pháp luật Việt Nam.

NHIỆM VỤ:
- Tóm tắt các văn bản luật đã phân tích
- Tổng hợp các ý kiến/góp ý của người dùng
- Tạo báo cáo tổng quan
- Highlight các điểm quan trọng

FORMAT BÁO CÁO:
📊 TỔNG QUAN
- Số văn bản tìm được: X
- Loại văn bản: [...]
- Khoảng thời gian: [...]

🎯 CÁC VĂN BẢN QUAN TRỌNG
1. [Tên văn bản] - [Tóm tắt]
2. ...

💬 Ý KIẾN NGƯỜI DÙNG
- [Tóm tắt ý kiến chính]

TRẢ LỜI BẰNG TIẾNG VIỆT."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "Tạo báo cáo tổng hợp:\n\n{analysis_results}")
        ])
        
        return prompt


# Test LLM connection
def test_llm_connection():
    """Test Gemini LLM connection"""
    try:
        log.info("Testing Gemini LLM connection...")
        llm = LLMConfig.get_gemini_llm()
        
        response = llm.invoke("Xin chào! Bạn là ai?")
        log.info(f"✓ LLM Response: {response.content[:100]}...")
        
        return True
        
    except Exception as e:
        log.error(f"✗ LLM connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test when run directly
    Config.validate(require_api_key=True)
    test_llm_connection()
