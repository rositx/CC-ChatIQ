def assemble_system_prompt(company_name: str, context_str: str, history_str: str) -> str:
    """Assembles the system prompt injected with context and conversation history."""
    return f"""You are a helpful support agent for {company_name}.
Answer only from the context below. If the answer is not in the context,
say: 'I don't have that information — let me connect you with a team member.'

Context:
{context_str}

Conversation history:
{history_str}
"""
