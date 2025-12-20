"""
Context processors to make LLM information available in all templates
"""
from django.conf import settings


def llm_info(request):
    """
    Add LLM provider information to template context
    """
    provider = getattr(settings, 'LLM_PROVIDER', 'groq').lower()
    use_llm = getattr(settings, 'USE_LLM', True)
    debug_mode = getattr(settings, 'DEBUG', False)
    
    # Helper function to check if API key is valid (not empty/whitespace)
    def is_valid_api_key(key):
        return key and isinstance(key, str) and key.strip() != ''
    
    # Check Groq first (default provider)
    if provider == 'groq' or provider == '':
        api_key = getattr(settings, 'GROQ_API_KEY', '')
        model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        
        if is_valid_api_key(api_key) and use_llm:
            llm_name = f"Groq ({model})"
            llm_status = "active"
            llm_description = f"Using Groq cloud-based AI model: {model}"
            llm_icon = "🚀"
            return {
                'llm_name': llm_name,
                'llm_status': llm_status,
                'llm_description': llm_description,
                'llm_icon': llm_icon,
                'llm_provider': 'groq',
                'use_llm': use_llm,
            }
        else:
            # Groq not configured properly
            if not use_llm:
                llm_name = "Rule-based (USE_LLM=false)"
                llm_description = "USE_LLM is set to false. Set USE_LLM=true in Railway Variables."
            elif not is_valid_api_key(api_key):
                llm_name = "Rule-based (Groq API key missing)"
                llm_description = "GROQ_API_KEY is not set or empty. Set it in Railway Variables. See RAILWAY_GROQ_SETUP.md"
            else:
                llm_name = "Rule-based (Groq not configured)"
                llm_description = "Groq API key not set. Set GROQ_API_KEY environment variable."
            
            llm_status = "fallback"
            llm_icon = "📝"
            return {
                'llm_name': llm_name,
                'llm_status': llm_status,
                'llm_description': llm_description,
                'llm_icon': llm_icon,
                'llm_provider': provider,
                'use_llm': use_llm,
            }
    
    # Determine which LLM is actually being used
    if not use_llm:
        llm_name = "Rule-based (No LLM)"
        llm_status = "disabled"
        llm_description = "USE_LLM is set to false. Set USE_LLM=true to enable LLM."
        llm_icon = "📝"
    elif provider == 'gemini':
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        model = getattr(settings, 'GEMINI_MODEL', 'gemini-pro')
        if is_valid_api_key(api_key) and use_llm:
            llm_name = f"Gemini ({model})"
            llm_status = "active"
            llm_description = f"Using Google Gemini AI model: {model}"
            llm_icon = "✨"
        else:
            llm_name = "Rule-based (Gemini not configured)"
            llm_status = "fallback"
            llm_description = "Gemini API key not set, using rule-based generation"
            llm_icon = "📝"
    elif provider == 'ollama':
        debug_mode = getattr(settings, 'DEBUG', False)
        # In production, don't show Ollama - show fallback status instead
        if not debug_mode:
            # Production/cloud - check if cloud LLMs are available
            groq_key = getattr(settings, 'GROQ_API_KEY', '')
            gemini_key = getattr(settings, 'GEMINI_API_KEY', '')
            if is_valid_api_key(groq_key) and use_llm:
                model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
                llm_name = f"Groq ({model}) - Auto-selected"
                llm_status = "active"
                llm_description = f"Ollama configured but using Groq (cloud LLM) in production"
                llm_icon = "🚀"
            elif is_valid_api_key(gemini_key) and use_llm:
                model = getattr(settings, 'GEMINI_MODEL', 'gemini-pro')
                llm_name = f"Gemini ({model}) - Auto-selected"
                llm_status = "active"
                llm_description = f"Ollama configured but using Gemini (cloud LLM) in production"
                llm_icon = "✨"
            else:
                llm_name = "Rule-based (Ollama not available in cloud)"
                llm_status = "fallback"
                llm_description = "Ollama is local-only. Configure Groq or Gemini for cloud deployment."
                llm_icon = "📝"
        else:
            # Local development - show Ollama
            base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
            model = getattr(settings, 'OLLAMA_MODEL', 'mistral')
            llm_name = f"Ollama ({model})"
            llm_status = "active"
            llm_description = f"Using local Ollama model: {model}"
            llm_icon = "🖥️"
    else:
        llm_name = "Rule-based (No LLM)"
        llm_status = "disabled"
        llm_description = "Using rule-based flashcard generation"
        llm_icon = "📝"
    
    return {
        'llm_name': llm_name,
        'llm_status': llm_status,
        'llm_description': llm_description,
        'llm_icon': llm_icon,
        'llm_provider': provider,
        'use_llm': use_llm,
    }

