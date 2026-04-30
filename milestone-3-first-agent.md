# Milestone 3: First Agent with Tools

**⏰ Time Commitment:** 4-5 evenings (8-10 hours)  
**When:** Week 3, Days 11-15  
**Prerequisites:** Milestone 2 complete and PR merged  
**Checkpoint:** ✓ Checkpoint 3 (after completion)  
**Next Milestone:** [Milestone 4: MCP-Powered Pipeline](milestone-4-mcp-pipeline.md)

---

## 🎯 Learning Objectives

By the end of this week, you will:
- Understand AI agent architecture
- Integrate Google ADK (Gemini)
- Engineer effective prompts
- Implement function calling / tool use
- Build NewsFilterAgent that uses tools
- Handle LLM errors gracefully
- Test AI agent behavior

**This is your first real AI code!** 🤖

---

## 📚 Week 3 Overview

```
Week 3: AI Agents
├── Evening 11 (Mon): Google ADK Setup + Agent Architecture
├── Evening 12 (Tue): NewsFilterAgent + Prompt Engineering
├── Evening 13 (Wed): Add Tool Use (Calculator, Search)
├── Evening 14 (Thu): Test Agent Behavior
└── Evening 15 (Fri): Integration + PR

Total: 8-10 hours over 4-5 evenings
```

---

## 📖 Required Reading (Before Evening 11)

**Read these first (45 minutes total):**

1. **Prompt Engineering Guide (20 min)**
   - https://www.promptingguide.ai/introduction/basics
   - Focus on: Few-shot prompting, Output formatting

2. **Google ADK Quickstart (15 min)**
   - https://ai.google.dev/tutorials/python_quickstart
   - Just the setup and first example

3. **Function Calling Overview (10 min)**
   - https://ai.google.dev/tutorials/function_calling_python_quickstart
   - Understand the concept

**Done reading?** Start Evening 11! 🚀

---

## 🌙 Evening 11: Google ADK Setup + Agent Architecture

**⏰ Time:** 1.5-2 hours  
**Goal:** Setup Google ADK and understand agent architecture

### **Timeline:**

```
7:30 PM - Start
├── 7:30-8:00 PM (30 min) - Google ADK setup
├── 8:00-8:30 PM (30 min) - Test Gemini API
├── 8:30-9:00 PM (30 min) - Design agent architecture
└── 9:00-9:20 PM (20 min) - Create BaseAgent
9:20 PM - Done!
```

---

### **Step 1: Install Google ADK (15 min)**

```bash
# Install Google Generative AI library
pip install google-generativeai

# Verify installation
python -c "import google.generativeai as genai; print('✅ Installed')"
```

**Configure API key:**

Check your `.env` file has:

```bash
GOOGLE_API_KEY=your_key_here
```

**Test connection:**

```python
# test_gemini.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Test
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Say hello!")

print(response.text)
print("✅ Google ADK working!")
```

```bash
python test_gemini.py

# Should print a greeting!
```

---

### **Step 2: Understand Gemini Basics (15 min)**

**Try a few examples:**

```python
# gemini_examples.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

model = genai.GenerativeModel('gemini-pro')

# Example 1: Simple completion
response = model.generate_content("Explain async/await in Python in one sentence")
print("Example 1:", response.text)

# Example 2: JSON output
prompt = """
Given this article title: "New AI Model Released"
Output JSON with these fields: relevant (boolean), reason (string)

{"relevant": true/false, "reason": "explanation"}
"""
response = model.generate_content(prompt)
print("\nExample 2:", response.text)

# Example 3: Few-shot learning
prompt = """
Classify articles as AI-related or not.

Examples:
Title: "GPT-4 Released" -> AI-related: Yes
Title: "Recipe for Pasta" -> AI-related: No
Title: "Machine Learning in Healthcare" -> AI-related: Yes

Now classify:
Title: "New JavaScript Framework"
"""
response = model.generate_content(prompt)
print("\nExample 3:", response.text)
```

```bash
python gemini_examples.py

# See how Gemini responds!
```

---

### **Step 3: Design Agent Architecture (30 min)**

**Create agent base class:**

**File:** `src/agents/base_agent.py`

```python
"""Base class for AI agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import google.generativeai as genai
import os


class BaseAgent(ABC):
    """
    Base class for all AI agents.
    
    Implements Template Method pattern:
    - execute() orchestrates the workflow
    - Subclasses implement specific steps
    """
    
    def __init__(self, model_name: str = "gemini-pro"):
        """
        Initialize agent.
        
        Args:
            model_name: Gemini model to use
        """
        self.model_name = model_name
        self.model = None
        self._configure_model()
    
    def _configure_model(self):
        """Configure Gemini model."""
        # Get API key from environment
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    async def execute(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Execute agent workflow (Template Method).
        
        Steps:
        1. Load input context
        2. Process with LLM
        3. Save results
        
        Args:
            input_path: Path to input markdown file
            output_path: Path to save output
            
        Returns:
            Result metadata
        """
        print(f"\n🤖 {self.__class__.__name__} starting...")
        
        # Step 1: Load
        context = await self._load_context(input_path)
        
        # Step 2: Process
        result = await self._process(context)
        
        # Step 3: Save
        await self._save_result(result, output_path)
        
        print(f"✅ {self.__class__.__name__} complete")
        
        return {
            'input_path': input_path,
            'output_path': output_path,
            'success': True
        }
    
    @abstractmethod
    async def _load_context(self, input_path: str) -> Dict[str, Any]:
        """
        Load input context.
        
        Subclasses implement how to read their input.
        """
        pass
    
    @abstractmethod
    async def _process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context with LLM.
        
        Subclasses implement their specific logic.
        """
        pass
    
    @abstractmethod
    async def _save_result(self, result: Dict[str, Any], output_path: str):
        """
        Save processing result.
        
        Subclasses implement how to save their output.
        """
        pass
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call Gemini with prompt.
        
        Helper method for subclasses.
        
        Args:
            prompt: Prompt to send
            
        Returns:
            LLM response text
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            raise
```

**Quick test:**

```python
# Test base agent
from src.agents.base_agent import BaseAgent

class TestAgent(BaseAgent):
    async def _load_context(self, input_path):
        return {"test": "data"}
    
    async def _process(self, context):
        response = self._call_llm("Say hello")
        return {"response": response}
    
    async def _save_result(self, result, output_path):
        print(f"Would save: {result}")

# Test it
import asyncio
agent = TestAgent()
asyncio.run(agent.execute("input.md", "output.md"))
```

---

### **Evening 11 Deliverable:**

✅ Google ADK installed and configured  
✅ Gemini API working  
✅ BaseAgent architecture defined  
✅ Template Method pattern implemented  
✅ Ready to build real agents  

**Time used:** 1.5-2 hours

---

## 🌙 Evening 12: NewsFilterAgent + Prompt Engineering

**⏰ Time:** 2 hours  
**Goal:** Build agent that filters AI-relevant articles

### **Timeline:**

```
7:30 PM - Start
├── 7:30-8:00 PM (30 min) - Design filtering logic
├── 8:00-8:45 PM (45 min) - Implement NewsFilterAgent
├── 8:45-9:15 PM (30 min) - Engineer prompts
└── 9:15-9:30 PM (15 min) - Test filtering
9:30 PM - Done!
```

---

### **Step 1: Design Filtering Logic (30 min)**

**What makes an article AI-relevant?**

```
Relevant:
✅ Machine learning
✅ Large language models
✅ AI research papers
✅ AI applications
✅ Neural networks
✅ Computer vision
✅ NLP

Not Relevant:
❌ General programming
❌ Web development
❌ DevOps
❌ Databases (unless AI-related)
```

**Output format:**

```json
{
  "relevant": true,
  "relevance_score": 8,
  "reasoning": "Discusses LLM training techniques",
  "key_topics": ["LLM", "training", "optimization"]
}
```

---

### **Step 2: Implement NewsFilterAgent (45 min)**

**File:** `src/agents/news_filter_agent.py`

```python
"""Agent that filters AI-relevant articles."""
import json
from typing import Dict, Any, List
from pathlib import Path
from src.agents.base_agent import BaseAgent
from src.models.article import Article
import re


class NewsFilterAgent(BaseAgent):
    """
    Filters articles for AI/ML relevance.
    
    Reads articles from markdown, uses LLM to judge relevance,
    saves filtered articles.
    """
    
    def __init__(self):
        super().__init__()
        self.relevance_threshold = 6  # Out of 10
    
    async def _load_context(self, input_path: str) -> Dict[str, Any]:
        """
        Load articles from markdown file.
        
        Args:
            input_path: Path to markdown file with articles
            
        Returns:
            Dict with articles list
        """
        print(f"📖 Loading articles from {input_path}")
        
        # Read markdown file
        content = Path(input_path).read_text()
        
        # Parse articles (simple parsing)
        articles = self._parse_markdown(content)
        
        print(f"   Found {len(articles)} articles")
        return {"articles": articles}
    
    def _parse_markdown(self, content: str) -> List[Dict]:
        """Parse markdown content to extract articles."""
        articles = []
        
        # Split by article separator
        sections = content.split('---')
        
        for section in sections:
            if '##' not in section:
                continue
            
            # Extract title (line starting with ##)
            title_match = re.search(r'## (.+)', section)
            if not title_match:
                continue
            
            title = title_match.group(1).strip()
            
            # Extract URL
            url_match = re.search(r'\*\*URL:\*\* (.+)', section)
            url = url_match.group(1).strip() if url_match else ""
            
            # Extract summary (last paragraph)
            lines = [l for l in section.split('\n') if l.strip() and not l.startswith('**')]
            summary = lines[-1] if lines else ""
            
            articles.append({
                'title': title,
                'url': url,
                'summary': summary
            })
        
        return articles
    
    async def _process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter articles using LLM.
        
        Args:
            context: Dict with articles
            
        Returns:
            Dict with filtered articles and metadata
        """
        articles = context['articles']
        print(f"🔍 Filtering {len(articles)} articles...")
        
        filtered = []
        
        for i, article in enumerate(articles):
            print(f"   [{i+1}/{len(articles)}] {article['title'][:50]}...")
            
            # Ask LLM to judge relevance
            judgment = self._judge_relevance(article)
            
            if judgment['relevant'] and judgment['relevance_score'] >= self.relevance_threshold:
                filtered.append({
                    **article,
                    'relevance_score': judgment['relevance_score'],
                    'reasoning': judgment['reasoning'],
                    'key_topics': judgment.get('key_topics', [])
                })
                print(f"      ✅ Relevant (score: {judgment['relevance_score']})")
            else:
                print(f"      ❌ Not relevant (score: {judgment['relevance_score']})")
        
        print(f"\n📊 Filtered: {len(filtered)}/{len(articles)} articles")
        
        return {
            'filtered_articles': filtered,
            'total_input': len(articles),
            'total_output': len(filtered)
        }
    
    def _judge_relevance(self, article: Dict) -> Dict:
        """
        Use LLM to judge article relevance.
        
        Args:
            article: Article dict with title, url, summary
            
        Returns:
            Dict with relevant, relevance_score, reasoning
        """
        prompt = f"""You are an expert AI/ML news analyst. Judge if this article is relevant to AI/ML.

Article:
Title: {article['title']}
Summary: {article['summary']}

Relevant topics include: Machine Learning, LLMs, Neural Networks, Computer Vision, NLP, AI Research, AI Applications, Deep Learning, Transformers, GPT, Stable Diffusion, AI Ethics, AI Safety

Output ONLY valid JSON with this exact format:
{{
  "relevant": true or false,
  "relevance_score": 1-10,
  "reasoning": "brief explanation",
  "key_topics": ["topic1", "topic2"]
}}

Examples:
- "GPT-4 Released" -> {{"relevant": true, "relevance_score": 10, "reasoning": "Major LLM release", "key_topics": ["LLM", "GPT"]}}
- "New JavaScript Framework" -> {{"relevant": false, "relevance_score": 1, "reasoning": "Web dev, not AI", "key_topics": []}}

Your JSON response:"""

        try:
            response = self._call_llm(prompt)
            
            # Extract JSON from response
            # LLM might wrap in ```json or similar
            json_text = response
            if '```json' in response:
                json_text = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                json_text = response.split('```')[1].split('```')[0]
            
            judgment = json.loads(json_text.strip())
            
            # Validate
            assert 'relevant' in judgment
            assert 'relevance_score' in judgment
            assert 'reasoning' in judgment
            
            return judgment
            
        except Exception as e:
            print(f"      ⚠️  Failed to parse LLM response: {e}")
            # Default to not relevant on error
            return {
                'relevant': False,
                'relevance_score': 0,
                'reasoning': f'Failed to judge: {e}',
                'key_topics': []
            }
    
    async def _save_result(self, result: Dict[str, Any], output_path: str):
        """
        Save filtered articles to markdown.
        
        Args:
            result: Dict with filtered_articles
            output_path: Path to save markdown
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        articles = result['filtered_articles']
        
        with open(output_path, 'w') as f:
            f.write(f"# Filtered AI/ML Articles\n\n")
            f.write(f"**Total Input:** {result['total_input']}\n")
            f.write(f"**Total Output:** {result['total_output']}\n")
            f.write(f"**Filter Rate:** {result['total_output']/result['total_input']*100:.1f}%\n\n")
            f.write("---\n\n")
            
            for article in articles:
                f.write(f"## {article['title']}\n\n")
                f.write(f"**URL:** {article['url']}\n")
                f.write(f"**Relevance Score:** {article['relevance_score']}/10\n")
                f.write(f"**Reasoning:** {article['reasoning']}\n")
                f.write(f"**Key Topics:** {', '.join(article['key_topics'])}\n\n")
                f.write(f"{article['summary']}\n\n")
                f.write("---\n\n")
        
        print(f"💾 Saved {len(articles)} filtered articles to {output_path}")
```

---

### **Step 3: Test NewsFilterAgent (15 min)**

```python
# test_filter_agent.py
import asyncio
from src.agents.news_filter_agent import NewsFilterAgent


async def test_filter():
    """Test filtering agent."""
    agent = NewsFilterAgent()
    
    # Use articles from Milestone 1
    result = await agent.execute(
        input_path="data/articles/all_articles.md",
        output_path="data/context/filtered_articles.md"
    )
    
    print(f"\n✅ Filtering complete!")
    print(f"   Input: {result['input_path']}")
    print(f"   Output: {result['output_path']}")


if __name__ == "__main__":
    asyncio.run(test_filter())
```

```bash
python test_filter_agent.py

# Should filter your articles!
# Check data/context/filtered_articles.md
```

---

### **Evening 12 Deliverable:**

✅ NewsFilterAgent implemented  
✅ Prompt engineering working  
✅ JSON parsing robust  
✅ Filtering logic tested  
✅ Filtered articles saved  

**Time used:** 2 hours

---

## 🌙 Evening 13: Add Tool Use

**⏰ Time:** 2 hours  
**Goal:** Add function calling / tools to agent

### **Timeline:**

```
7:30 PM - Start
├── 7:30-8:00 PM (30 min) - Understand function calling
├── 8:00-8:45 PM (45 min) - Implement tools (calculator, search)
└── 8:45-9:30 PM (45 min) - Integrate tools with agent
9:30 PM - Done!
```

---

### **Step 1: Create Simple Tools (30 min)**

**File:** `src/tools/calculator.py`

```python
"""Simple calculator tool."""
from typing import Dict, Any


def calculator(expression: str) -> Dict[str, Any]:
    """
    Evaluate mathematical expression.
    
    Args:
        expression: Math expression (e.g., "2 + 2", "10 * 5")
        
    Returns:
        Dict with result or error
    """
    try:
        # Safe eval with limited scope
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "success": True,
            "result": result,
            "expression": expression
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "expression": expression
        }


# Tool schema for LLM
CALCULATOR_SCHEMA = {
    "name": "calculator",
    "description": "Evaluate mathematical expressions. Use for arithmetic calculations.",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
            }
        },
        "required": ["expression"]
    }
}


# Test
if __name__ == "__main__":
    print(calculator("2 + 2"))
    print(calculator("10 * 5 + 3"))
    print(calculator("invalid"))
```

**File:** `src/tools/web_search.py`

```python
"""Simple web search tool (mock for now)."""
from typing import Dict, Any, List


def web_search(query: str, num_results: int = 3) -> Dict[str, Any]:
    """
    Search the web (mocked for now).
    
    In reality, would use real search API.
    For learning, returns mock results.
    
    Args:
        query: Search query
        num_results: Number of results
        
    Returns:
        Dict with results
    """
    # Mock results for demonstration
    mock_results = [
        {
            "title": f"Result for: {query}",
            "url": f"https://example.com/search?q={query}",
            "snippet": f"This is a mock search result for '{query}'"
        }
    ] * num_results
    
    return {
        "success": True,
        "query": query,
        "num_results": num_results,
        "results": mock_results
    }


# Tool schema
WEB_SEARCH_SCHEMA = {
    "name": "web_search",
    "description": "Search the web for current information. Use when you need real-time data.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (1-10)",
                "default": 3
            }
        },
        "required": ["query"]
    }
}


# Test
if __name__ == "__main__":
    print(web_search("latest AI news"))
```

---

### **Step 2: Add Function Calling to Agent (45 min)**

**Update BaseAgent with tool support:**

```python
# In base_agent.py, add:

from google.generativeai.types import FunctionDeclaration, Tool

class BaseAgent(ABC):
    def __init__(self, model_name: str = "gemini-pro", tools: List[Dict] = None):
        self.model_name = model_name
        self.tools = tools or []
        self.model = None
        self.tool_functions = {}
        self._configure_model()
    
    def _configure_model(self):
        """Configure Gemini model with tools."""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")
        
        genai.configure(api_key=api_key)
        
        # Configure with tools if provided
        if self.tools:
            # Create function declarations
            functions = []
            for tool_schema in self.tools:
                func_decl = FunctionDeclaration(
                    name=tool_schema['name'],
                    description=tool_schema['description'],
                    parameters=tool_schema['parameters']
                )
                functions.append(func_decl)
            
            # Create tools
            tools = Tool(function_declarations=functions)
            self.model = genai.GenerativeModel(
                self.model_name,
                tools=[tools]
            )
        else:
            self.model = genai.GenerativeModel(self.model_name)
    
    def register_tool_function(self, name: str, function):
        """Register actual function for a tool."""
        self.tool_functions[name] = function
    
    def _call_llm_with_tools(self, prompt: str) -> str:
        """
        Call LLM with tool support.
        
        Handles function calling loop.
        """
        chat = self.model.start_chat()
        response = chat.send_message(prompt)
        
        # Check for function calls
        while response.candidates[0].content.parts:
            part = response.candidates[0].content.parts[0]
            
            # If function call
            if hasattr(part, 'function_call'):
                func_call = part.function_call
                func_name = func_call.name
                func_args = dict(func_call.args)
                
                print(f"   🔧 Tool call: {func_name}({func_args})")
                
                # Execute function
                if func_name in self.tool_functions:
                    result = self.tool_functions[func_name](**func_args)
                    print(f"   📊 Tool result: {result}")
                    
                    # Send result back to LLM
                    response = chat.send_message(
                        Part(function_response=FunctionResponse(
                            name=func_name,
                            response=result
                        ))
                    )
                else:
                    raise ValueError(f"Tool {func_name} not registered")
            else:
                # Text response, we're done
                return response.text
        
        return response.text
```

---

### **Step 3: Create Tool-Enhanced Agent (45 min)**

**File:** `src/agents/enhanced_filter_agent.py`

```python
"""News filter agent with tool use."""
from src.agents.news_filter_agent import NewsFilterAgent
from src.tools.calculator import calculator, CALCULATOR_SCHEMA
from src.tools.web_search import web_search, WEB_SEARCH_SCHEMA


class EnhancedFilterAgent(NewsFilterAgent):
    """
    Filter agent that can use tools.
    
    Extends NewsFilterAgent with calculator and search.
    """
    
    def __init__(self):
        # Initialize with tools
        super().__init__()
        self.tools = [CALCULATOR_SCHEMA, WEB_SEARCH_SCHEMA]
        self._configure_model()  # Reconfigure with tools
        
        # Register tool functions
        self.register_tool_function('calculator', calculator)
        self.register_tool_function('web_search', web_search)
    
    def _judge_relevance(self, article: Dict) -> Dict:
        """
        Judge relevance with tool access.
        
        LLM can now call calculator or search if needed.
        """
        prompt = f"""You are an AI/ML news analyst with access to tools.

Article:
Title: {article['title']}
Summary: {article['summary']}

Judge if this is AI/ML relevant. You can use:
- calculator: for any math calculations
- web_search: to verify claims or get context

Output JSON:
{{
  "relevant": true/false,
  "relevance_score": 1-10,
  "reasoning": "explanation (mention if you used tools)",
  "key_topics": ["topic1", "topic2"]
}}
"""
        
        try:
            # Use tool-enabled LLM call
            response = self._call_llm_with_tools(prompt)
            
            # Parse JSON (same as before)
            json_text = response
            if '```json' in response:
                json_text = response.split('```json')[1].split('```')[0]
            
            judgment = json.loads(json_text.strip())
            return judgment
            
        except Exception as e:
            print(f"      ⚠️  Error: {e}")
            return {
                'relevant': False,
                'relevance_score': 0,
                'reasoning': f'Error: {e}',
                'key_topics': []
            }
```

**Test it:**

```python
# test_enhanced_agent.py
import asyncio
from src.agents.enhanced_filter_agent import EnhancedFilterAgent


async def test_tools():
    """Test agent with tools."""
    agent = EnhancedFilterAgent()
    
    result = await agent.execute(
        input_path="data/articles/all_articles.md",
        output_path="data/context/enhanced_filtered.md"
    )
    
    print(f"\n✅ Enhanced filtering complete!")
    print(f"   Check output for tool usage mentions")


if __name__ == "__main__":
    asyncio.run(test_tools())
```

---

### **Evening 13 Deliverable:**

✅ Calculator tool implemented  
✅ Web search tool (mock) created  
✅ Function calling integrated  
✅ EnhancedFilterAgent with tools  
✅ Tool execution tested  

**Time used:** 2 hours

---

## 🌙 Evening 14: Testing & Integration

**⏰ Time:** 1.5-2 hours  
**Goal:** Comprehensive testing and integration

### **Timeline:**

```
7:30 PM - Start
├── 7:30-8:15 PM (45 min) - Write agent tests
├── 8:15-9:00 PM (45 min) - Integration with Milestone 1
└── 9:00-9:20 PM (20 min) - End-to-end test
9:20 PM - Done!
```

---

### **Step 1: Write Agent Tests (45 min)**

```python
# tests/test_news_filter_agent.py
import pytest
from src.agents.news_filter_agent import NewsFilterAgent
from pathlib import Path
import tempfile


@pytest.mark.asyncio
async def test_agent_filters_articles():
    """Test agent filters correctly."""
    # Create temp input file
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = Path(tmpdir) / "input.md"
        output_file = Path(tmpdir) / "output.md"
        
        # Write test articles
        input_file.write_text("""
## GPT-4 Released by OpenAI

**URL:** https://example.com/gpt4

OpenAI announces GPT-4 with enhanced capabilities.

---

## New JavaScript Framework

**URL:** https://example.com/js

React alternative for web development.
""")
        
        # Run agent
        agent = NewsFilterAgent()
        result = await agent.execute(str(input_file), str(output_file))
        
        # Check output
        assert output_file.exists()
        content = output_file.read_text()
        
        # Should include GPT-4
        assert "GPT-4" in content
        
        # Should not include JS framework (probably)
        # Note: LLM behavior can vary


@pytest.mark.asyncio
async def test_tool_usage():
    """Test tools are callable."""
    from src.tools.calculator import calculator
    from src.tools.web_search import web_search
    
    # Test calculator
    result = calculator("2 + 2")
    assert result['success']
    assert result['result'] == 4
    
    # Test search
    result = web_search("AI news")
    assert result['success']
    assert len(result['results']) > 0
```

---

### **Step 2: Integration (45 min)**

**Create end-to-end pipeline:**

**File:** `src/pipeline.py`

```python
"""Complete pipeline: Fetch -> Filter."""
import asyncio
from src.orchestrator import FetchOrchestrator
from src.agents.news_filter_agent import NewsFilterAgent
from pathlib import Path


async def run_pipeline():
    """
    Run complete pipeline.
    
    1. Fetch articles (Milestone 1)
    2. Filter with AI agent (Milestone 3)
    """
    print("=" * 60)
    print("  Complete Pipeline: Fetch + Filter")
    print("=" * 60)
    
    # Step 1: Fetch articles
    print("\n📰 Step 1: Fetching articles...")
    orchestrator = FetchOrchestrator()
    articles = await orchestrator.fetch_all()
    
    fetch_output = Path("data/articles/all_articles.md")
    print(f"✅ Fetched {len(articles)} articles")
    print(f"   Saved to: {fetch_output}")
    
    # Step 2: Filter with AI
    print("\n🤖 Step 2: Filtering with AI...")
    agent = NewsFilterAgent()
    filter_output = Path("data/context/filtered_articles.md")
    
    result = await agent.execute(
        input_path=str(fetch_output),
        output_path=str(filter_output)
    )
    
    print(f"✅ Filtering complete")
    print(f"   Filtered articles: {filter_output}")
    
    print("\n" + "=" * 60)
    print("🎉 Pipeline complete!")
    print(f"   1. Fetched: {fetch_output}")
    print(f"   2. Filtered: {filter_output}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
```

**Test full pipeline:**

```bash
python src/pipeline.py

# Should fetch then filter!
```

---

### **Evening 14 Deliverable:**

✅ Agent tests written  
✅ Tool tests passing  
✅ End-to-end pipeline working  
✅ Integration tested  

**Time used:** 1.5-2 hours

---

## 🌙 Evening 15: Polish & PR

**⏰ Time:** 1 hour  
**Goal:** Clean up and submit PR

### **Quick cleanup and PR creation:**

```bash
# Format code
black src/ tests/

# Run all tests
pytest tests/ -v

# Create PR
git add .
git commit -m "feat: AI agent with tool use and filtering"
git push origin feature/milestone-3-agent
```

**PR Description:**

```markdown
# Milestone 3: First Agent with Tools

## Summary

Built AI agent that filters articles using Gemini LLM with tool calling support.

## What I Built

✅ **NewsFilterAgent**
- Uses Gemini to judge article relevance
- Filters for AI/ML content
- Returns relevance scores and reasoning

✅ **Tool Use**
- Calculator tool
- Web search tool (mock)
- Function calling integration

✅ **BaseAgent Architecture**
- Template Method pattern
- Reusable for future agents
- Tool registration system

## Skills Learned

- Google ADK integration
- Prompt engineering
- Function calling / tool use
- LLM error handling
- Agent architecture patterns

## Testing

- Agent filtering tested
- Tool execution verified
- End-to-end pipeline working

## Files Created

**Agents:**
- src/agents/base_agent.py
- src/agents/news_filter_agent.py
- src/agents/enhanced_filter_agent.py

**Tools:**
- src/tools/calculator.py
- src/tools/web_search.py

**Pipeline:**
- src/pipeline.py

**Tests:**
- tests/test_news_filter_agent.py

## Next Steps

Ready for Milestone 4: MCP-Powered Pipeline
```

---

## 🎉 Milestone 3 Complete!

### **What You Accomplished:**

✅ Built first AI agent  
✅ Integrated Google ADK (Gemini)  
✅ Engineered effective prompts  
✅ Implemented function calling  
✅ Created reusable agent architecture  
✅ End-to-end pipeline working  

### **Skills Gained (15 skills):**

1. Google ADK setup and configuration
2. Gemini API integration
3. Prompt engineering basics
4. Few-shot learning
5. JSON output formatting
6. Function calling / tool use
7. Tool schema design
8. Agent architecture (Template Method)
9. LLM error handling
10. Async agent execution
11. Context loading/saving
12. Agent testing strategies
13. Tool registration systems
14. Integration patterns
15. Pipeline orchestration

---

## 📝 Checkpoint 3: PR Review

**Required Approvals:** 2 reviewers

**See:** [Checkpoint 3 Rubric](../rubrics/checkpoint-3-rubric.md)

---

## ➡️ Next Steps

**After PR Approval:**

Proceed to [Milestone 4: MCP-Powered Pipeline](milestone-4-mcp-pipeline.md)

You'll build MCP servers and create a multi-agent pipeline!

**Time:** 5-7 evenings (10-14 hours)

---

**Questions?** Ask in Slack: `#ai-agent-onboarding-cohort-[X]`

**Milestone 3 Complete** ✅  
**Time Spent:** 8-10 hours over 4-5 evenings  
**Next:** Milestone 4 (Week 4)
