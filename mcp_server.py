# TUTORIAL UPDATE (mcp v1 -> v2): server class renamed.
#   Old (mcp 1.x, what the tutorial uses):
#       from mcp.server.fastmcp import FastMCP
#       mcp = FastMCP("DocumentMCP", log_level="ERROR")
#   New (mcp 2.x): `FastMCP` is now `MCPServer`, imported from
#       `mcp.server.mcpserver`. The old `mcp.server.fastmcp` module no longer
#       exists (ModuleNotFoundError). Every submodule moved the same way:
#       mcp.server.fastmcp.* -> mcp.server.mcpserver.*
#   Decorators (@mcp.tool / @mcp.resource / @mcp.prompt) and `log_level` are unchanged.
#   (The separate PyPI package "fastmcp" is a different project and is not used here.)
import textwrap

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceError, ToolError
from mcp.server.mcpserver.prompts import base
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
    description="Read the contents of a document and return it as a string.",
)
def read_document(doc_id: str = Field(description="Id of the document to read")) -> str:
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
    description="Edit a document by replacing a string in the document's content with the new string",
)
def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited"),
    old_str: str = Field(
        description="The text to replace. Must match exactly, including white space."
    ),
    new_str: str = Field(description="The new text to insert in place of the old text"),
) -> None:
    """Replace occurrences of a string in a document with a new string.

    Every occurrence of old_str is replaced. The document is modified in place
    in the in-memory store; nothing is returned.

    Args:
        doc_id: Id of the document to edit.
        old_str: The text to replace. Must match exactly, including whitespace.
        new_str: The text to insert in place of old_str.

    Raises:
        ToolError: If no document with the given id exists, or if old_str is no
        found in the document.

    """
    if doc_id not in docs:
        raise ToolError(f"Doc with id {doc_id} not found")

    if old_str not in docs[doc_id]:
        raise ToolError(f"Text to replace was not found in {doc_id}")

    docs[doc_id] = docs[doc_id].replace(old_str, new_str)


@mcp.resource("docs://documents", mime_type="application/json")
def list_docs() -> list[str]:
    """Return the ids of all available documents.

    Served at docs://documents as JSON (a list of id strings).
    """
    return list(docs.keys())


@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
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


@mcp.prompt(
    name="format",
    description="Rewrites the contents of the document in Markdown format.",
)
def format_document(
    doc_id: str = Field(description="Id of the document to format"),
) -> list[base.Message]:
    """Build a prompt asking the model to rewrite a document in Markdown.

    Args:
        doc_id: Id of the document to reformat.

    Returns:
        A single user message that tells the model to reformat the documen
        and save it with the `edit_document` tool.
    """
    prompt = textwrap.dedent(f"""
    Your goal is to reformat a document to be written with markdown syntax.

    The id of the document you need to reformat is:
    <document_id>
    {doc_id}
    </document_id>

    Add in headers, bullet points, tables, etc as necessary. Feel free to add in structure.
    Use the 'edit_document' tool to edit the document after the document has been reformatted.
    """).strip()

    return [base.UserMessage(prompt)]


@mcp.prompt(name="summarize", description="Summarizes the given document.")
def summarize_document(
    doc_id: str = Field(description="Id of the document to summarize"),
) -> list[base.Message]:
    """Build a prompt asking the model to summarize a document.

    Args:
        doc_id: Id of the document to summarize.

    Returns:
        A single user message that tells the model to summarize the document.
    """
    prompt = textwrap.dedent(f"""
    Your goal is to summarize a document.

    The id of the document you need to summarize is:
    <document_id>
    {doc_id}
    </document_id>

    Use the 'read_doc_contents' tool to read the document first, then write a
    concise summary (at most 5 sentences) covering its main points.
    Do not edit the document.
    """).strip()

    return [base.UserMessage(prompt)]


if __name__ == "__main__":
    mcp.run(transport="stdio")
