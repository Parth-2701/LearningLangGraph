import os
print("GROQ key exists:", bool(os.getenv("GROQ_API_KEY")))
print("LangSmith key exists:", bool(os.getenv("LANGCHAIN_API_KEY")))
print("Tracing:", os.getenv("LANGCHAIN_TRACING_V2"))
print("Project:", os.getenv("LANGCHAIN_PROJECT"))