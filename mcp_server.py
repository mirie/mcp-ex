# TUTORIAL DRIFT (mcp v1 -> v2): server class renamed.
#   Old (mcp 1.x, what the tutorial uses):
#       from mcp.server.fastmcp import FastMCP
#       mcp = FastMCP("DocumentMCP", log_level="ERROR")
#   New (mcp 2.x): `FastMCP` is now `MCPServer`, imported from
#       `mcp.server.mcpserver`. The old `mcp.server.fastmcp` module no longer
#       exists (ModuleNotFoundError). Every submodule moved the same way:
#       mcp.server.fastmcp.* -> mcp.server.mcpserver.*
#   Decorators (@mcp.tool / @mcp.resource / @mcp.prompt) and `log_level` are unchanged.
#   (The separate PyPI package "fastmcp" is a different project and is not used here.)
from mcp.server.mcpserver import MCPServer

# TUTORIAL DRIFT (mcp v1 -> v2): errors raised inside tools.
#   Old (mcp 1.x): `raise ValueError("...")` inside a tool sent the exception
#       text to the client as the tool's error message.
#   New (mcp 2.x): an unexpected exception (ValueError, KeyError, ...) is logged
#       with a traceback on the server, and the client only sees the generic
#       "Error executing tool <name>". To send a message the model can actually
#       read and act on, raise `ToolError` (resources: `ResourceError`).
from mcp.server.mcpserver.exceptions import ResourceError, ToolError
from pydantic import Field

mcp = MCPServer("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a document and return it as a string."
)
def read_document(
    doc_id: str = Field(description="Id of the document to read")
) -> str:
    """Return the full text contents of a document.

    Args:
        doc_id: Id of the document to read (e.g. "report.pdf").

    Returns:
        The document's contents as a string.

    Raises:
        ToolError: If no document with the given id exists.
    """
    if doc_id not in docs:
        raise ToolError(f"Doc with id {doc_id} not found")

    return docs[doc_id]


@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the document's content with the new string"
)
def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited"),
    old_str: str = Field(description="The text to replace. Must match exactly, including white space."),
    new_str: str = Field(description="The new text to insert in place of the old text")
) -> None:
    """Replace occurrences of a string in a document with a new string.

    Every occurrence of old_str is replaced. The document is modified in place
    in the in-memory store; nothing is returned.

    Args:
        doc_id: Id of the document to edit.
        old_str: The text to replace. Must match exactly, including whitespace.
        new_str: The text to insert in place of old_str.

    Raises:
        ToolError: If no document with the given id exists.
    """
    if doc_id not in docs:
        raise ToolError(f"Doc with id {doc_id} not found")

    docs[doc_id] = docs[doc_id].replace(old_str, new_str)

@mcp.resource(
    "docs://documents",
    mime_type="application/json"
)
def list_docs() -> list[str]:
    """Return the ids of all available documents.

    Served at docs://documents as JSON (a list of id strings).
    """
    return list(docs.keys())

@mcp.resource(
    "docs://documents/{doc_id}",
    mime_type="text/plain"
)
def fetch_doc(doc_id: str) -> str:
    """Return the contents of a single document.

    Served at docs://documents/{doc_id} as plain text.

    Args:
        doc_id: Id of the document to fetch (e.g. "report.pdf").

    Returns:
        The document's contents as a string.

    Raises:
        ResourceError: If no document with the given id exists.
    """
    if doc_id not in docs:
        raise ResourceError(f"Doc with id {doc_id} not found")
    return docs[doc_id]


#   TUTORIAL DRIFT (mcp v1 -> v2), resources:
#     - `@mcp.resource("docs://documents", mime_type="application/json")` and
#       `@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")` are
#       unchanged. Decorator arguments and handler signatures are the same.
#     - Old (1.x): raising ValueError for a missing doc id reached the client.
#       New (2.x): raise `ResourceError` (mcp.server.mcpserver.exceptions) so the
#       message is delivered; a plain ValueError is masked, as with tools.
#     - New (2.x): a URI that matches no resource returns JSON-RPC error -32602
#       ("Unknown resource"). A `ResourceError` raised inside a handler (e.g. a
#       missing doc id on the template resource) arrives as -32603 with your
#       message intact. The client sees both as `MCPError`.
#
# TODO: Write a prompt to rewrite a doc in markdown format
# TODO: Write a prompt to summarize a doc
#   TUTORIAL DRIFT (mcp v1 -> v2), prompts:
#     - Old (1.x): `from mcp.server.fastmcp.prompts import base`
#       New (2.x): `from mcp.server.mcpserver.prompts import base`
#       (`base.UserMessage` and `base.AssistantMessage` are unchanged; they are
#       also exported straight from `mcp.server.mcpserver`.)
#     - `@mcp.prompt(name=..., description=...)` is unchanged.
#     - New (2.x): a prompt function may also return a bare content block.


if __name__ == "__main__":
    mcp.run(transport="stdio")
