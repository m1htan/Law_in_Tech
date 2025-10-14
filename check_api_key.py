"""
Check and validate API key setup
"""
import os
from pathlib import Path
from dotenv import load_dotenv


def check_api_key():
    """Check if API key is properly configured"""
    print("\n" + "="*60)
    print("API KEY CONFIGURATION CHECK")
    print("="*60)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("\n❌ ERROR: .env file not found!")
        print("\n📝 Solution:")
        print("1. Copy .env.example to .env:")
        print("   cp .env.example .env")
        print("2. Edit .env and add your API key")
        return False
    
    print("\n✅ .env file exists")
    
    # Load environment variables
    load_dotenv()
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY", "")
    
    print(f"\nAPI Key value: {api_key[:20]}..." if len(api_key) > 20 else f"API Key: '{api_key}'")
    
    if not api_key:
        print("\n❌ ERROR: GOOGLE_API_KEY is empty")
        print("\n📝 Solution:")
        print("1. Open .env file")
        print("2. Replace the line:")
        print("   GOOGLE_API_KEY=your_google_api_key_here")
        print("   with your actual key:")
        print("   GOOGLE_API_KEY=AIzaSy...")
        print("3. Save the file")
        return False
    
    if api_key == "your_google_api_key_here":
        print("\n❌ ERROR: GOOGLE_API_KEY still has placeholder value")
        print("\n📝 Solution:")
        print("1. Get your API key from: https://makersuite.google.com/app/apikey")
        print("2. Open .env file")
        print("3. Replace 'your_google_api_key_here' with your actual key")
        print("4. Save the file")
        return False
    
    if len(api_key) < 30:
        print("\n⚠️ WARNING: API key looks too short")
        print("   A valid Gemini API key usually starts with 'AIza' and is ~39 characters")
        return False
    
    if not api_key.startswith("AIza"):
        print("\n⚠️ WARNING: API key doesn't look like a Gemini key")
        print("   Gemini API keys typically start with 'AIza'")
        return False
    
    print("\n✅ API key looks valid!")
    print(f"   Length: {len(api_key)} characters")
    print(f"   Starts with: {api_key[:10]}...")
    
    # Test with actual import
    print("\n" + "-"*60)
    print("Testing LLM connection...")
    print("-"*60)
    
    try:
        from src.agents.llm_config import LLMConfig
        
        llm = LLMConfig.get_gemini_llm()
        response = llm.invoke("Xin chào, trả lời bằng 1 câu ngắn")
        
        print("\n✅ LLM connection successful!")
        print(f"Response: {response.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ LLM connection failed: {e}")
        print("\n📝 Possible issues:")
        print("1. API key is invalid")
        print("2. No internet connection")
        print("3. Gemini API is down")
        print("4. API key doesn't have proper permissions")
        return False


def show_instructions():
    """Show detailed instructions"""
    print("\n" + "="*60)
    print("HOW TO GET & SET GOOGLE GEMINI API KEY")
    print("="*60)
    
    print("""
1️⃣ GET API KEY:
   a) Go to: https://makersuite.google.com/app/apikey
   b) Click "Create API key"
   c) Copy the key (starts with AIza...)

2️⃣ SET API KEY:
   a) Open file: .env
   b) Find line: GOOGLE_API_KEY=your_google_api_key_here
   c) Replace with: GOOGLE_API_KEY=AIza...YOUR_KEY_HERE
   d) Save file

3️⃣ VERIFY:
   Run: python3 check_api_key.py

Example .env file:
┌─────────────────────────────────────────┐
│ GOOGLE_API_KEY=AIzaSyABC123...xyz789   │
│ MAX_CONCURRENT_REQUESTS=3               │
│ REQUEST_DELAY=2                         │
│ ...                                     │
└─────────────────────────────────────────┘
""")


if __name__ == "__main__":
    result = check_api_key()
    
    if not result:
        show_instructions()
        print("\n" + "="*60)
        print("❌ API key not configured properly")
        print("="*60)
        print("\n👉 Follow instructions above to fix")
        exit(1)
    else:
        print("\n" + "="*60)
        print("✅ Everything is ready!")
        print("="*60)
        print("\n👉 You can now run: python3 test_ai_agent.py")
        exit(0)
