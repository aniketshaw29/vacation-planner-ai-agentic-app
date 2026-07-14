import os


def get_llm(provider: str = "groq"):
    """Return a LangChain chat model for the requested provider."""
    provider = provider.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="llama-3.1-70b-versatile",
            temperature=0,
            streaming=True,
            max_tokens=4096,
            api_key=os.environ["GROQ_API_KEY"],
        )

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0,
            streaming=True,
            google_api_key=os.environ["GOOGLE_API_KEY"],
        )

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            streaming=True,
            api_key=os.environ["OPENAI_API_KEY"],
        )

    raise ValueError(f"Unknown provider: {provider!r}. Choose 'groq', 'gemini', or 'openai'.")


def available_providers() -> list[str]:
    """Return the list of providers that have an API key configured."""
    providers = []
    if os.environ.get("GROQ_API_KEY"):
        providers.append("groq")
    if os.environ.get("GOOGLE_API_KEY"):
        providers.append("gemini")
    if os.environ.get("OPENAI_API_KEY"):
        providers.append("openai")
    return providers
