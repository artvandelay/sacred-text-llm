# Sacred Texts Agentic Chat Guide

## 🎯 **What is the Agent?**

The agentic chat (`agent_chat.py`) is an advanced AI that doesn't just search once and respond. Instead, it:

1. **Plans** what to search for based on your question
2. **Searches** multiple refined queries in parallel
3. **Reflects** on whether it has enough evidence
4. **Iterates** until confident or reaches max attempts
5. **Responds** with a comprehensive, well-researched answer

## 🚀 **Quick Start**

### **Basic Usage**
```bash
# Start the agent
python agent_chat.py

# Ask complex questions
> "How do Buddhism and Christianity approach forgiveness differently?"
```

### **OpenRouter Setup (Recommended)**
```bash
# 1. Get API key from: https://openrouter.ai/keys
# 2. Set environment variables
export OPENROUTER_API_KEY="your-key-here"
export LLM_PROVIDER="openrouter"

# 3. Run agent with GPT-4/Claude
python agent_chat.py
```

## 📊 **Agent Behavior Examples**

### **Simple Question (1-2 iterations)**
```
Q: "What is compassion in Buddhism?"

🧠 Planning: Focus on Buddhist compassion teachings
🔍 Searching: 2 parallel queries
    • Buddhist compassion meditation practices
    • Karuna and loving-kindness in Buddhist texts
🤔 Reflecting: Confidence: 82% → Good evidence
✅ Complete in 1 iteration
```

### **Complex Question (3-4 iterations)**
```
Q: "How do different traditions understand the relationship between suffering and spiritual growth?"

🧠 Planning: Multi-tradition perspective needed
🔍 Searching: 3 parallel queries
    • Buddhist teachings on suffering as path to enlightenment
    • Christian theodicy and redemptive suffering
    • Islamic perspectives on trials and spiritual purification
🤔 Reflecting: Confidence: 65% → Need more traditions

🧠 Planning: Add more traditions and philosophical perspectives  
🔍 Searching: 3 parallel queries
    • Hindu concepts of karma and spiritual evolution
    • Jewish wisdom on suffering and meaning
    • Stoic philosophy on suffering as teacher
🤔 Reflecting: Confidence: 88% → Excellent coverage
✅ Complete in 2 iterations
```

## ⚙️ **Configuration Options**

### **Core Settings**
```bash
# Agent behavior
export MAX_ITERATIONS_PER_QUERY=4      # How many search rounds
export CONFIDENCE_THRESHOLD=0.75       # Stop when this confident  
export MAX_PARALLEL_QUERIES=3          # Simultaneous searches
export MAX_TOTAL_EVIDENCE_CHUNKS=15    # Limit total evidence

# UI preferences  
export SHOW_AGENT_PROGRESS=true        # Show thinking process
export SHOW_SEARCH_QUERIES=true        # Display search queries
export SHOW_CONFIDENCE_SCORES=true     # Show confidence percentages
export COLLAPSE_COMPLETED_STEPS=true   # Clean up finished steps
```

### **LLM Providers**
```bash
# Local Ollama (free, private)
export LLM_PROVIDER="ollama"
export OLLAMA_CHAT_MODEL="qwen3:30b-a3b"

# OpenRouter (better quality, costs ~$0.01-0.10 per query)
export LLM_PROVIDER="openrouter"  
export OPENROUTER_CHAT_MODEL="anthropic/claude-3.5-sonnet"
```

## 🎭 **When to Use Each Interface**

### **Use `query.py` for:**
- Quick, simple questions
- Single-fact lookups
- Testing the system
- When you want immediate results

### **Use `chat.py` for:**
- Conversational interaction
- Multiple related questions
- When you want a polished interface
- General spiritual guidance

### **Use `agent_chat.py` for:**
- Complex, multi-faceted questions
- Cross-tradition comparisons
- Research-quality responses
- When you want comprehensive evidence
- Deep philosophical inquiries

## 🔧 **Troubleshooting**

### **Agent Not Starting**
```bash
# Check vector store
python check_progress.py

# Test basic components
python -c "from agent_chat import SacredTextsAgent; print('✅ Import successful')"
```

### **Poor Agent Performance**
```bash
# Increase iterations for complex questions
export MAX_ITERATIONS_PER_QUERY=6

# Lower confidence threshold for more thorough searching
export CONFIDENCE_THRESHOLD=0.65

# Use better LLM for planning/reflection
export LLM_PROVIDER="openrouter"
```

### **Progress UI Issues**
```bash
# Disable rich UI if having terminal issues
export SHOW_AGENT_PROGRESS=false

# Or use simple progress display
python -c "from agent_ui import SimpleProgressUI; print('✅ Simple UI available')"
```

## 💡 **Pro Tips**

### **Ask Better Questions**
- ❌ "Tell me about love"
- ✅ "How do Buddhist and Christian traditions define divine love differently?"

- ❌ "What is meditation?"  
- ✅ "Compare contemplative practices across Hindu, Buddhist, and Christian mystical traditions"

### **Use Specific Terminology**
- Include tradition names: "Buddhist," "Christian," "Islamic," "Hindu"
- Use spiritual terms: "enlightenment," "salvation," "dharma," "grace"
- Ask for comparisons: "compare," "contrast," "different perspectives"

### **Leverage Agent Strengths**
- Ask multi-part questions that require synthesis
- Request cross-tradition analysis
- Seek comprehensive coverage of complex topics
- Ask for evidence-based responses

## 📈 **Performance Comparison**

| Feature | query.py | chat.py | agent_chat.py |
|---------|----------|---------|---------------|
| **Speed** | ⚡ Instant | ⚡ Fast | 🔄 Thoughtful |
| **Depth** | 📄 Basic | 📄 Good | 📚 Comprehensive |
| **Evidence** | 5 passages | 5 passages | Up to 15+ passages |
| **Planning** | None | None | ✅ Strategic |
| **Iteration** | Single shot | Single shot | ✅ Multi-round |
| **Confidence** | Unknown | Unknown | ✅ Measured |
| **Best For** | Quick facts | Conversation | Research |

The agent is designed for when you want the AI to **think deeply** and **search comprehensively** rather than just give a quick response. It's the difference between asking a chatbot vs. consulting a research assistant.
