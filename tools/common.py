from marvin import ai_fn

@ai_fn
def summarize(text: str) -> str:
    """Returns a summary of the given text content."""