from langchain.tools import BaseTool


class ReplyTool(BaseTool):
    name: str = "reply"
    description: str = "Use this to communicate with the user, such as clarifying questions or informing them of success/failure of a request."

    def _run(self, tool_input: str) -> str:
        return tool_input

    async def _arun(self, tool_input: str) -> str:
        return self._run(tool_input)
