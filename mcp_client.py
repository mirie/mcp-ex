import sys
import asyncio
from typing import Any
from contextlib import AsyncExitStack
from mcp import Client, ClientSession, StdioServerParameters, types


class MCPClient:
    def __init__(
        self,
        command: str,
        args: list[str],
        env: dict[str, str] | None = None,
    ):
        self._command = command
        self._args = args
        self._env = env
        self._client: Client | None = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    # TUTORIAL DRIFT (mcp v1 -> v2): connect via the high-level `Client`.
    #   Old (mcp 1.x, what the tutorial uses):
    #       from mcp.client.stdio import stdio_client
    #       stdio_transport = await self._exit_stack.enter_async_context(
    #           stdio_client(server_params)
    #       )
    #       _stdio, _write = stdio_transport
    #       self._session = await self._exit_stack.enter_async_context(
    #           ClientSession(_stdio, _write)
    #       )
    #       await self._session.initialize()
    #
    #   New (mcp 2.x): `Client` accepts `StdioServerParameters` directly. It
    #       starts the server subprocess, builds the session, and runs the
    #       connection handshake itself when entered (mode="auto" by default:
    #       it tries the newer `server/discover` handshake, then falls back to
    #       `initialize`). No `stdio_client`, no manual `ClientSession`, no
    #       explicit `initialize()`.
    #   `self._client.session` is the underlying `ClientSession`, which
    #   `session()` below returns, so `self.session().list_tools()` etc. still work.
    async def connect(self) -> None:
        server_params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=self._env,
        )
        self._client = await self._exit_stack.enter_async_context(
            Client(server_params)
        )

    def session(self) -> ClientSession:
        if self._client is None:
            raise ConnectionError(
                "Client session not initialized. Call connect() first."
            )
        return self._client.session

    async def list_tools(self) -> list[types.Tool]:
        """Return the tools currently exposed by the MCP server.

        Follows pagination cursors, so servers that split their tool list
        across several pages are fully covered.

        Returns:
            All tools from the server, in the order it returned them.

        Raises:
            ConnectionError: If connect() hasn't been called yet.
        """
        tools: list[types.Tool] = []
        cursor: str | None = None
        while True:
            page = await self.session().list_tools(
                params=types.PaginatedRequestParams(cursor=cursor)
            )
            tools.extend(page.tools)
            cursor = page.next_cursor
            if cursor is None:
                break
        return tools

    async def call_tool(
        self, tool_name: str, tool_input: dict
    ) -> types.CallToolResult:
        """Call a tool on the MCP server and return its result as-is.

        Tool failures are not raised. An unknown tool, invalid arguments, or
        an error raised inside the tool all come back as a normal result with
        `is_error=True` and the message in `content`.

        Args:
            tool_name: Name of the tool to call.
            tool_input: Arguments for the tool, matching its input schema.
                Use an empty dict for tools that take no arguments.

        Returns:
            The server's CallToolResult.

        Raises:
            ConnectionError: If connect() hasn't been called yet.
        """
        return await self.session().call_tool(tool_name, tool_input)

    async def list_prompts(self) -> list[types.Prompt]:
        # TODO: Return a list of prompts defined by the MCP server
        return []

    async def get_prompt(self, prompt_name, args: dict[str, str]):
        # TODO: Get a particular prompt defined by the MCP server
        #   TUTORIAL DRIFT (mcp v1 -> v2):
        #     - `(await self.session().get_prompt(prompt_name, args)).messages`
        #       is unchanged.
        #     - Fields on prompt/message types are snake_case in 2.x (was camelCase),
        #       e.g. `PromptMessage.content`, `GetPromptResult.messages` are the
        #       same single words, but any multi-word field (e.g. `mimeType` on
        #       embedded resources) is now `mime_type`.
        return []

    async def read_resource(self, uri: str) -> Any:
        # TODO: Read a resource, parse the contents and return it
        #   TUTORIAL DRIFT (mcp v1 -> v2):
        #     - Old (1.x):
        #           from pydantic import AnyUrl
        #           result = await self.session().read_resource(AnyUrl(uri))
        #           resource = result.contents[0]
        #           if isinstance(resource, types.TextResourceContents):
        #               if resource.mimeType == "application/json":
        #                   return json.loads(resource.text)
        #               return resource.text
        #     - New (2.x): resource URIs are plain `str` (no AnyUrl). Call
        #       `read_resource(uri)` directly. `resource.mimeType` is now
        #       `resource.mime_type`. `isinstance(..., types.TextResourceContents)`
        #       and `json.loads(resource.text)` are unchanged.
        return []

    async def cleanup(self) -> None:
        await self._exit_stack.aclose()
        self._client = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()


# For testing
async def main():
    async with MCPClient(
        command="uv",
        args=["run", "mcp_server.py"],
    ) as _client:
        result = await _client.list_tools()
        print(result)
        #pass


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
