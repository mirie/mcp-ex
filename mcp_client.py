import sys
import asyncio
from typing import Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


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
        self._session: ClientSession | None = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    # TUTORIAL DRIFT (mcp v1 -> v2): the connection pattern here is unchanged.
    #   `stdio_client` + `ClientSession` + `initialize()` inside an AsyncExitStack
    #   works as in 1.x (v2 negotiates protocol 2025-11-25 over this path).
    #   New in 2.x (optional, not used here): a higher-level `mcp.Client` that
    #   takes `StdioServerParameters` directly and defaults to mode="auto".
    async def connect(self) -> None:
        server_params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=self._env,
        )
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        _stdio, _write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(_stdio, _write)
        )
        await self._session.initialize()

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError(
                "Client session not initialized. Call connect() first."
            )
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        # TODO: Return a list of tools defined by the MCP server
        #   TUTORIAL DRIFT (mcp v1 -> v2):
        #     - `(await self.session().list_tools()).tools` is unchanged.
        #     - Old (1.x): `list_tools(cursor="...")` for pagination.
        #       New (2.x): the `cursor` argument was removed; pass
        #       `params=PaginatedRequestParams(cursor=...)` (from mcp.types)
        #       and read `result.next_cursor` (was `nextCursor`).
        #     - Returned `Tool` objects use snake_case: `tool.input_schema`
        #       (was `inputSchema`), `tool.output_schema` (was `outputSchema`).
        return []

    async def call_tool(
        self, tool_name: str, tool_input: dict
    ) -> types.CallToolResult | None:
        # TODO: Call a particular tool and return the result
        #   TUTORIAL DRIFT (mcp v1 -> v2):
        #     - `await self.session().call_tool(tool_name, tool_input)` is unchanged.
        #     - Old (1.x): check `result.isError`; `result.structuredContent`.
        #       New (2.x): `result.is_error`; `result.structured_content`.
        #     - Tool failures still come back as a normal result with
        #       `is_error=True` (they are not raised). New (2.x): the message is
        #       only readable if the server raised `ToolError`; a plain
        #       exception arrives as "Error executing tool <name>".
        return None

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
        self._session = None

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
        pass


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
