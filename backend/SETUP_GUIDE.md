# 🚀 Slack Integration Setup Guide

## ❌ Current Error: Missing Supabase Configuration

The application is failing because it cannot connect to Supabase. Here's how to fix it:

## 🔧 Quick Fix Steps

### 1. Create Environment File
```bash
# Copy the example environment file
cp .env.example .env
```

### 2. Configure Required Variables
Edit the `.env` file with your actual values:

```bash
# Database Configuration (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# AI Configuration (REQUIRED for Article Generation)
OPENAI_API_KEY=sk-your-openai-key-here
SERPER_API_KEY=your-serper-dev-api-key-here
```

### 3. Get Your Supabase Credentials

1. **Go to [Supabase Dashboard](https://supabase.com/dashboard)**
2. **Select your project** (or create a new one)
3. **Go to Settings → API**
4. **Copy the values:**
   - **Project URL** → `SUPABASE_URL`
   - **anon/public key** → `SUPABASE_ANON_KEY`

### 4. Get Your API Keys

#### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy it to `OPENAI_API_KEY`

#### Serper API Key (for web search)
1. Go to [Serper.dev](https://serper.dev/)
2. Sign up and get your API key
3. Copy it to `SERPER_API_KEY`

### 5. Restart the Server
```bash
poetry run uvicorn main:app --reload
```

## 📋 Complete Environment Variables

### Required for Basic Operation
```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# AI Services
OPENAI_API_KEY=sk-your-openai-key-here
SERPER_API_KEY=your-serper-dev-api-key-here
```

### Optional for Enhanced Features
```bash
# Claude AI (optional)
USE_CLAUDE_FOR_ARTICLES=false
CLAUDE_API_KEY=your-claude-api-key-here

# Slack Integration (if using Slack features)
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
```

## 🧪 Test Your Setup

After configuring the environment variables:

```bash
# Test the article generation endpoints
python test_article_endpoints.py

# Or start the server and visit
# http://localhost:8000/api/docs
```

## 🔍 Troubleshooting

### Error: "Missing Supabase configuration"
- ✅ Check that `.env` file exists in the backend directory
- ✅ Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` are set
- ✅ Ensure no extra spaces or quotes in the values

### Error: "OpenAI API key not found"
- ✅ Set `OPENAI_API_KEY` in your `.env` file
- ✅ Verify the API key is valid and has credits

### Error: "Serper API key not found"
- ✅ Set `SERPER_API_KEY` in your `.env` file
- ✅ Get a free API key from [Serper.dev](https://serper.dev/)

## 🎯 Next Steps

Once the environment is configured:

1. **Test the API**: Visit `http://localhost:8000/api/docs`
2. **Run the test script**: `python test_article_endpoints.py`
3. **Generate articles**: Use the `/api/v1/articles/research-brief` endpoint

## 📞 Need Help?

If you're still having issues:
1. Check the server logs for specific error messages
2. Verify all environment variables are correctly set
3. Ensure your Supabase project is active and accessible

---

**Status**: Ready for production with CrewAI 0.201.1 integration! 🚀
