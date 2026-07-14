import os

# Priority order: first key found is the default provider shown in the UI.
_PROVIDER_PRIORITY = ["gemini", "groq", "openai", "anthropic"]


def get_llm(provider: str = "gemini"):
    """Return a configured LangChain chat model for the requested provider."""
    provider = provider.lower()

    if provider == "gemini":
        # Available stable Gemini model options you can switch to:
        #   gemini-2.5-flash-lite  — fastest, cheapest
        #   gemini-2.5-flash       — default, best price-performance
        #   gemini-2.5-pro         — most capable, higher quota usage
        #   gemini-3.5-flash       — best for agentic tasks, check quota
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            streaming=True,
            google_api_key=os.environ["GOOGLE_API_KEY"],
        )

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="llama-3.1-70b-versatile",
            temperature=0,
            streaming=True,
            max_tokens=4096,
            api_key=os.environ["GROQ_API_KEY"],
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            streaming=True,
            api_key=os.environ["OPENAI_API_KEY"],
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-3-5-haiku-20241022",
            temperature=0,
            streaming=True,
            api_key=os.environ["ANTHROPIC_API_KEY"],
        )

    raise ValueError(
        f"Unknown provider: {provider!r}. "
        "Choose from: gemini, groq, openai, anthropic"
    )


def available_providers() -> list[str]:
    """Return providers that have an API key configured, in priority order."""
    key_map = {
        "gemini": "GOOGLE_API_KEY",
        "groq": "GROQ_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    return [p for p in _PROVIDER_PRIORITY if os.environ.get(key_map[p])]


def default_provider() -> str:
    """Return the highest-priority available provider, or raise if none configured."""
    providers = available_providers()
    if not providers:
        raise RuntimeError(
            "No LLM API key configured. Set at least one of: "
            "GOOGLE_API_KEY, GROQ_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY"
        )
    return providers[0]
