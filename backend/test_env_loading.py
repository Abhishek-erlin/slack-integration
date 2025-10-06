#!/usr/bin/env python3
"""
Test environment variable loading
"""

import os
from dotenv import load_dotenv

def test_env_loading():
    """Test if environment variables are loaded correctly"""
    print("🧪 Testing Environment Variable Loading...")
    print("=" * 50)
    
    # Load .env file
    result = load_dotenv()
    print(f"📁 .env file loaded: {result}")
    
    # Check if .env file exists
    env_exists = os.path.exists('.env')
    print(f"📄 .env file exists: {env_exists}")
    
    if not env_exists:
        print("❌ .env file not found!")
        print("💡 Please copy .env.example to .env and configure it")
        return False
    
    # Test critical variables
    test_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY", 
        "OPENAI_API_KEY",
        "SERPER_API_KEY"
    ]
    
    print("\n🔍 Checking Environment Variables:")
    print("-" * 40)
    
    all_good = True
    for var in test_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if len(value) > 12:
                display_value = f"{value[:8]}...{value[-4:]}"
            else:
                display_value = "***"
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Not set")
            all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 All environment variables are loaded correctly!")
        return True
    else:
        print("❌ Some environment variables are missing!")
        return False

if __name__ == "__main__":
    test_env_loading()
