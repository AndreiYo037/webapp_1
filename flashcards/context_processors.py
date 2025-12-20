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
    
    # Determine which LLM is actually being used
    if not use_llm:
        llm_name = "Rule-based (No LLM)"
        llm_status = "disabled"
        llm_description = "Using rule-based flashcard generation"
        llm_icon = "📝"
    elif provider == 'groq':
        api_key = getattr(settings, 'GROQ_API_KEY', '')
        model = getattr(settings, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
        if api_key:
            llm_name = f"Groq ({model})"
            llm_status = "active"
            llm_description = f"Using Groq cloud-based AI model: {model}"
            llm_icon = "🚀"
        else:
            llm_name = "Rule-based (Groq not configured)"
            llm_status = "fallback"
            llm_description = "Groq API key not set, using rule-based generation"
            llm_icon = "📝"
    elif provider == 'gemini':
        api_key = getattr(settings, 'GEMINI_API_KEY', '')
        model = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')
        if api_key:
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

