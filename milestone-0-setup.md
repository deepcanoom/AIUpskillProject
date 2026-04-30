# Milestone 0: Local Setup & Architecture

**⏰ Time Commitment:** 1 evening (1-2 hours)  
**When:** Day 1  
**Prerequisites:** None  
**Next Milestone:** [Milestone 1: Async News Fetcher](milestone-1-async-fetcher.md)

---

## 🎯 Learning Objectives

By the end of this evening, you will:
- Have a fully configured local development environment
- Understand the project architecture
- Run your first "hello world" test
- Be ready to start coding tomorrow

**This is NOT a coding milestone** - just setup so you can hit the ground running!

---

## 📋 Your Evening Timeline (1-2 hours)

```
7:30 PM - Start
├── 7:30-7:45 PM (15 min) - Clone repo & read README
├── 7:45-8:00 PM (15 min) - Create venv & install dependencies
├── 8:00-8:20 PM (20 min) - Get API keys
├── 8:20-8:30 PM (10 min) - Configure .env file
├── 8:30-8:40 PM (10 min) - Run automated verification
└── 8:40-9:00 PM (20 min) - Read architecture overview
9:00 PM - Done! ✅
```

**No coding tonight** - save your energy for tomorrow!

---

## ✅ Task 1: Clone & Explore (15 minutes)

### **Step 1: Clone the repository**

```bash
# Clone to your preferred location
cd ~/projects  # or wherever you keep code
git clone https://github.com/your-org/ai-agent-onboarding.git
cd ai-agent-onboarding
```

### **Step 2: Explore the structure**

```bash
# Take a quick look around
ls -la

# You should see:
# - src/          # Your code goes here
# - tests/        # Your tests go here
# - docs/         # Documentation and milestones
# - data/         # Output files (created automatically)
# - requirements.txt
# - README.md
# - .env.example
```

### **Step 3: Read the README**

```bash
# Open in your editor
code .  # VS Code
# or
open -a "Sublime Text" .
# or your preferred editor
```

Read `README.md` for 5 minutes - get the big picture.

**Time check:** ✅ Should be ~7:45 PM (15 min used)

---

## ✅ Task 2: Create Virtual Environment (15 minutes)

### **Why virtual environments?**
Isolates project dependencies from system Python. Essential for clean development.

### **Step 1: Create venv**

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# You should see (venv) in your terminal prompt
```

### **Step 2: Upgrade pip**

```bash
pip install --upgrade pip
```

### **Step 3: Install dependencies**

```bash
# Install all project dependencies
pip install -r requirements.txt

# This installs:
# - aiohttp (async HTTP)
# - feedparser (RSS parsing)
# - google-generativeai (Google ADK)
# - mcp (Model Context Protocol)
# - pytest (testing)
# - black, isort, pylint (code quality)
# - and more...

# Should take 2-3 minutes
```

### **Step 4: Verify installation**

```bash
# Check Python version
python --version
# Should show: Python 3.11.x or higher

# Check key packages
python -c "import aiohttp; import feedparser; print('✅ Core packages installed')"
```

**Time check:** ✅ Should be ~8:00 PM (30 min used)

---

## ✅ Task 3: Get API Keys (20 minutes)

You need 2 free API keys. Both have generous free tiers.

### **API Key 1: NewsAPI (5 min)**

**Purpose:** Fetch news articles

**Steps:**
1. Go to: https://newsapi.org/
2. Click "Get API Key"
3. Sign up (free account)
4. Copy your API key

**Free tier:** 100 requests/day (plenty for learning!)

### **API Key 2: Google AI Studio (15 min)**

**Purpose:** Access Gemini for AI agents

**Steps:**
1. Go to: https://ai.google.dev/
2. Click "Get started"
3. Sign in with Google account
4. Click "Get API key" in AI Studio
5. Create new API key
6. Copy the key

**Free tier:** 60 requests/minute (excellent for learning!)

**Save both keys** - you'll use them in next step.

**Time check:** ✅ Should be ~8:20 PM (50 min used)

---

## ✅ Task 4: Configure Environment (10 minutes)

### **Step 1: Copy environment template**

```bash
# Copy the example file
cp .env.example .env

# Open .env in your editor
code .env  # or your editor
```

### **Step 2: Add your API keys**

Edit `.env`:

```bash
# .env file

# NewsAPI - paste your key here
NEWSAPI_KEY=your_newsapi_key_here

# Google AI - paste your key here
GOOGLE_API_KEY=your_google_api_key_here

# These are fine as defaults
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### **Step 3: Verify .env is ignored**

```bash
# Check .gitignore
cat .gitignore | grep .env

# Should see:
# .env
# .env.local

# This means your API keys won't be committed to git ✅
```

**IMPORTANT:** Never commit `.env` to git! Your keys are secrets.

**Time check:** ✅ Should be ~8:30 PM (60 min used)

---

## ✅ Task 5: Run Verification (10 minutes)

### **Step 1: Run automated verification script**

```bash
# Run verification
python scripts/verify_setup.py

# This checks:
# ✅ Python version
# ✅ Dependencies installed
# ✅ API keys configured
# ✅ Directory structure
# ✅ Import paths work
```

### **Expected output:**

```
🔍 Verifying AI Agent Onboarding Setup...

✅ Python version: 3.11.5
✅ Virtual environment: Active
✅ Dependencies: All installed
✅ API keys: Configured
✅ Project structure: Valid
✅ Import paths: Working

🎉 Setup complete! Ready to start Milestone 1.

Next steps:
1. Read docs/architecture/overview.md
2. Start Milestone 1 tomorrow
3. Join Slack: #ai-agent-onboarding-cohort-[X]
```

### **If you see errors:**

**Python version wrong:**
```bash
# Install Python 3.11+ from python.org
# Then recreate venv with correct version
```

**Missing dependencies:**
```bash
pip install -r requirements.txt
```

**API keys not found:**
```bash
# Check .env file has both keys
# No quotes needed around keys
# No spaces around =
```

**Time check:** ✅ Should be ~8:40 PM (70 min used)

---

## ✅ Task 6: Read Architecture (20 minutes)

### **Step 1: Open architecture doc**

```bash
# Open in browser or editor
open docs/architecture/overview.md
# or
code docs/architecture/overview.md
```

### **Step 2: Read and understand**

**Focus on these sections (20 min):**

1. **System Overview (5 min)**
   - What you're building
   - Why this architecture
   - Main components

2. **Data Flow (5 min)**
   - How data moves through system
   - Markdown files as context
   - Why this approach

3. **Technology Stack (5 min)**
   - Python + async/await
   - Google ADK for AI
   - MCP for tools
   - SQLite for data

4. **Week-by-week preview (5 min)**
   - What you build each week
   - How it all connects
   - Final deliverable

**Don't code anything** - just read and understand the big picture.

### **Key Concepts to Grasp:**

**1. Everything runs locally**
- No servers to deploy
- No cloud setup
- All on your laptop

**2. Markdown as context**
- Agents communicate via markdown files
- Human-readable
- Git-friendly
- Easy to debug

**3. Progressive complexity**
- Week 1: Async basics
- Week 2: Clean code
- Week 3: AI agents
- Week 4: MCP + multi-agent
- Week 5: Quality

**Time check:** ✅ Should be ~9:00 PM (90 min used)

---

## 🎉 Milestone 0 Complete!

### **What You Accomplished:**

✅ Development environment ready  
✅ Dependencies installed  
✅ API keys configured  
✅ Verification passed  
✅ Architecture understood  

### **Your Laptop Now Has:**

```
ai-agent-onboarding/
├── venv/                    # Your isolated environment ✅
├── .env                     # Your API keys (secret) ✅
├── src/                     # Ready for your code
├── tests/                   # Ready for your tests
└── data/                    # Will be created automatically
```

### **Ready for Tomorrow:**

Tomorrow evening (Milestone 1, Day 1), you'll write your first async code!

---

## 📚 Optional Reading (Weekend/Extra Time)

If you finish early or want to prepare for Week 1:

**Async Python Primer:**
- https://realpython.com/async-io-python/
- 20 minutes, excellent introduction

**Markdown Guide:**
- https://www.markdownguide.org/basic-syntax/
- 10 minutes, quick reference

**Don't code yet!** Just read if you have extra time.

---

## ❓ Troubleshooting

### **"Python 3.11 not found"**

**Solution:**
```bash
# Install from python.org
# Then:
python3.11 -m venv venv
```

### **"pip install fails"**

**Solution:**
```bash
# Upgrade pip first
pip install --upgrade pip

# Then retry
pip install -r requirements.txt
```

### **"API key not working"**

**Solution:**
```bash
# Check .env format:
NEWSAPI_KEY=abc123  # No quotes, no spaces around =

# Test NewsAPI:
curl "https://newsapi.org/v2/top-headlines?country=us&apiKey=YOUR_KEY"

# Should return JSON
```

### **"Import errors"**

**Solution:**
```bash
# Make sure venv is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# You should see (venv) in prompt

# Verify Python
which python  # Should point to venv/bin/python
```

### **Still stuck?**

Ask in Slack: `#ai-agent-onboarding-cohort-[X]`

Include:
- Your OS (Mac/Windows/Linux)
- Python version: `python --version`
- Error message (full text)

---

## 📝 Checkpoint Questions

Before moving to Milestone 1, verify you understand:

**Q: Where does your code live?**  
A: `src/` directory

**Q: Where are your API keys?**  
A: `.env` file (never commit this!)

**Q: What database will you use?**  
A: SQLite (local file, no server needed)

**Q: Where will articles be saved?**  
A: `data/articles/` as markdown files

**Q: Do you need to deploy to cloud?**  
A: NO! Everything runs on your laptop

If you can answer these, you're ready! ✅

---

## ➡️ Next Steps

**Tomorrow Evening (Day 2):**

Start [Milestone 1: Async News Fetcher](milestone-1-async-fetcher.md)

You'll build your first async code - a HackerNews fetcher!

**Time required:** 1.5-2 hours

**What you'll learn:**
- async/await basics
- HTTP requests with aiohttp
- File I/O
- Basic testing

See you tomorrow! 🚀

---

## 🎯 Success Criteria

- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] API keys configured in .env
- [ ] Verification script passes
- [ ] Architecture document read
- [ ] Ready to code tomorrow

**All checked?** You're done for tonight! Get some rest. 😴

---

**Questions?** Ask in Slack: `#ai-agent-onboarding-cohort-[X]`

**Milestone 0 Complete** ✅  
**Time Spent:** 1-2 hours  
**Next:** Milestone 1 (Tomorrow evening)
