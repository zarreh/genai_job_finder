# Universal LLM Configuration System

This document explains the new Universal LLM Configuration System that makes it extremely easy to switch between different LLM models (OpenAI, Ollama, etc.) across all modules in the application.

## 🎯 Quick Start

### Change Models in 30 Seconds

1. **Open `genai_job_finder/llm_config.py`** in the project
2. **Edit the variables at the top:**
   ```python
   # Data Cleaner Module
   data_cleaner_llm = "llama3.2"

   # Query Definition Module  
   query_definition_llm = "gpt-3.5-turbo"

   # Frontend Chat Module
   frontend_chat_llm = "llama3.2"

   # Frontend Resume Analysis Module
   frontend_resume_llm = "gpt-3.5-turbo"
   ```
3. **Restart your application** - Done! 🎉

## 📁 New Files Added

- **`genai_job_finder/llm_config.py`** - Main configuration file (edit this to change models)
- **`genai_job_finder/llm_factory.py`** - Universal LLM factory (no need to edit)
- **`demo_universal_llm.py`** - Demo script showing model switching

## 🔧 Available Models

### OpenAI Models
- `gpt-3.5-turbo`
- `gpt-4` 
- `gpt-4-turbo`
- `gpt-4o-mini` ✨ *New!*
- `gpt-5-nano` ✨ *New!* (placeholder for future release)

### Ollama Models  
- `llama3.2`
- `llama3.1`
- `mistral`
- `codellama`
- `gemma2:27b` ✨ *New!*

## 🛠️ How It Works

### Before (Complex)
```python
# Each module had its own complex configuration
config = CleanerConfig(
    ollama_model="llama3.2",
    ollama_base_url="http://localhost:11434",
    ollama_temperature=0.1,
    ollama_max_tokens=1000
)
```

### After (Simple)
```python
# Just change one variable in llm_config.py
data_cleaner_llm = "mistral"  # Switch to Mistral
```

## 📋 Module Coverage

✅ **Data Cleaner** - Experience extraction, employment validation, etc.  
✅ **Query Definition** - Resume analysis and job query generation  
✅ **Frontend Chat** - Career advisor chat service  
✅ **Frontend Resume** - Resume analysis service  
❌ **LinkedIn Parser** - No LLM usage (no changes needed)

## 🔄 Migration Summary

### What Changed
- **Simplified Configuration**: One file (`llm_config.py`) controls all models
- **Universal Factory**: One factory (`llm_factory.py`) creates all LLMs
- **No Complex Classes**: Removed complicated configuration classes
- **Easy Switching**: Change models by editing simple variables

### What Stayed the Same
- **All Existing Functionality**: Everything works exactly as before
- **API Compatibility**: All modules still work with existing code
- **Model Support**: Still supports both OpenAI and Ollama

## 🧪 Testing

Run the demo to see model switching in action:
```bash
python demo_universal_llm.py
```

## 🔑 Environment Variables

For OpenAI models, make sure you have:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
OPENAI_API_KEY=your-api-key-here
```

## ❓ Troubleshooting

### "OpenAI API key is required"
- Set your `OPENAI_API_KEY` environment variable
- Or switch to Ollama models (no API key needed)

### "Model 'xyz' not found"
- Check the available models list in `llm_config.py`
- Make sure you spelled the model name correctly

### Import Errors
- The system uses absolute imports that should work from the project root
- If you get import errors, make sure you're running from the correct directory

## 🚀 Adding New Models

To add a new model, edit `MODEL_CONFIGS` in `genai_job_finder/llm_config.py`:

```python
MODEL_CONFIGS = {
    # ... existing models ...
    "new-model-name": {
        "provider": "ollama",  # or "openai"
        "model": "new-model-name",
        "temperature": 0.1,
        "max_tokens": 1000,
        "base_url": "http://localhost:11434"  # for Ollama
    }
}
```

## 🎉 Benefits

1. **Super Easy**: Change models by editing one variable
2. **No Restart Needed**: Changes take effect immediately  
3. **Universal**: Works across all modules consistently
4. **Maintainable**: One place to configure everything
5. **Extensible**: Easy to add new models or providers
6. **Clear**: No confusing classes or complex configuration

---

**Need Help?** Check the demo script or look at `genai_job_finder/llm_config.py` for examples!