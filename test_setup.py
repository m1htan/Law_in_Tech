"""
Test script to verify installation and setup
"""
import sys
import os

def test_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 10:
        print("  → Python version is compatible (3.10+)")
        return True
    else:
        print("  ✗ Python version should be 3.10 or higher")
        return False

def test_imports():
    """Test if key packages can be imported"""
    packages = [
        ("langchain", "LangChain"),
        ("langgraph", "LangGraph"),
        ("langchain_google_genai", "LangChain Google GenAI"),
        ("crawl4ai", "Crawl4AI"),
        ("dotenv", "python-dotenv"),
        ("pandas", "Pandas"),
    ]
    
    all_success = True
    for module, name in packages:
        try:
            __import__(module)
            print(f"✓ {name} imported successfully")
        except ImportError as e:
            print(f"✗ {name} failed to import: {e}")
            all_success = False
    
    return all_success

def test_config():
    """Test configuration file"""
    try:
        from src.config import Config
        print("✓ Configuration loaded successfully")
        print(f"  → PDF output: {Config.PDF_OUTPUT_DIR}")
        print(f"  → Text output: {Config.TEXT_OUTPUT_DIR}")
        print(f"  → Date range: {Config.START_YEAR}-{Config.END_YEAR}")
        print(f"  → Target websites: {len(Config.TARGET_WEBSITES)}")
        
        # Check if API key is set
        if Config.GOOGLE_API_KEY and Config.GOOGLE_API_KEY != "your_google_api_key_here":
            print("✓ Google API Key is configured")
        else:
            print("⚠ Google API Key not set (please update .env file)")
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def test_directories():
    """Check if required directories exist"""
    from src.config import Config
    dirs = [Config.PDF_OUTPUT_DIR, Config.TEXT_OUTPUT_DIR, Config.LOG_DIR]
    
    all_exist = True
    for dir_path in dirs:
        if dir_path.exists():
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Directory missing: {dir_path}")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Vietnamese Legal Crawler Setup")
    print("=" * 60)
    print()
    
    print("[1/4] Testing Python Version...")
    result1 = test_python_version()
    print()
    
    print("[2/4] Testing Package Imports...")
    result2 = test_imports()
    print()
    
    print("[3/4] Testing Configuration...")
    result3 = test_config()
    print()
    
    print("[4/4] Testing Directories...")
    result4 = test_directories()
    print()
    
    print("=" * 60)
    if all([result1, result2, result3, result4]):
        print("✓ All tests passed! Setup is complete.")
        print("\nNext steps:")
        print("1. Update your Google API Key in the .env file")
        print("2. Run the crawler (coming in next steps)")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        if not result2:
            print("\nTo install missing packages, run:")
            print("  pip install -r requirements.txt")
    print("=" * 60)

if __name__ == "__main__":
    main()
