#!/usr/bin/env python3
"""
Environment Configuration Checker
Helps diagnose missing environment variables and configuration issues.
"""

import os
from dotenv import load_dotenv

def check_environment():
    """Check all required environment variables"""
    print("🔍 Checking Environment Configuration...")
    print("=" * 50)
    
    # Load .env file if it exists
    env_file = ".env"
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"✅ Found .env file: {env_file}")
    else:
        print(f"❌ No .env file found. Please copy .env.example to .env")
        return False
    
    print()
    
    # Required variables
    required_vars = {
        "SUPABASE_URL": "Your Supabase project URL",
        "SUPABASE_ANON_KEY": "Your Supabase anonymous key",
        "OPENAI_API_KEY": "Your OpenAI API key",
        "SERPER_API_KEY": "Your Serper.dev API key"
    }
    
    # Optional variables
    optional_vars = {
        "USE_CLAUDE_FOR_ARTICLES": "Enable Claude for article generation",
        "CLAUDE_API_KEY": "Your Claude API key",
        "SLACK_BOT_TOKEN": "Your Slack bot token",
        "SLACK_SIGNING_SECRET": "Your Slack signing secret"
    }
    
    print("📋 Required Environment Variables:")
    print("-" * 40)
    
    all_required_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "key" in var.lower() or "token" in var.lower():
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Not set - {description}")
            all_required_set = False
    
    print()
    print("🔧 Optional Environment Variables:")
    print("-" * 40)
    
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            if "key" in var.lower() or "token" in var.lower():
                display_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"⚪ {var}: Not set - {description}")
    
    print()
    print("=" * 50)
    
    if all_required_set:
        print("🎉 All required environment variables are set!")
        print("🚀 You can now start the server with: poetry run uvicorn main:app --reload")
        return True
    else:
        print("❌ Some required environment variables are missing.")
        print("📖 Please check SETUP_GUIDE.md for detailed instructions.")
        return False

def test_supabase_connection():
    """Test Supabase connection"""
    try:
        from supabase import create_client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Cannot test Supabase connection - missing credentials")
            return False
        
        print("🔗 Testing Supabase connection...")
        client = create_client(supabase_url, supabase_key)
        
        # Try a simple query to test connection
        result = client.table("articles").select("count", count="exact").execute()
        print("✅ Supabase connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        return False

def test_openai_connection():
    """Test OpenAI connection"""
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ Cannot test OpenAI connection - missing API key")
            return False
        
        print("🤖 Testing OpenAI connection...")
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print("✅ OpenAI connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Slack Integration - Environment Checker")
    print("=" * 50)
    print()
    
    # Check environment variables
    env_ok = check_environment()
    
    if env_ok:
        print()
        print("🧪 Testing Connections...")
        print("-" * 30)
        
        # Test connections
        supabase_ok = test_supabase_connection()
        openai_ok = test_openai_connection()
        
        print()
        if supabase_ok and openai_ok:
            print("🎉 All systems ready! You can start the server now.")
        else:
            print("⚠️  Some connections failed. Check your credentials and try again.")
    
    print()
    print("📖 For detailed setup instructions, see SETUP_GUIDE.md")
