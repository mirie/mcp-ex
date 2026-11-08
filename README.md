# MCP Chat

MCP Chat is a command-line interface application that enables interactive chat capabilities with AI models through the Anthropic API. The application supports document retrieval, command-based prompts, and extensible tool integrations via the MCP (Model Context Protocol) architecture.

## Reference

I'm following this tutorial: [Introduction to Model Context Protocol](https://anthropic-partners.skilljar.com/introduction-to-model-context-protocol/) (Anthropic Skilljar).

The tutorial is written for `mcp` 1.x, but this project runs on `mcp` 2.x (currently 2.3.0). Where the code differs from the tutorial, there's a `TUTORIAL DRIFT (mcp v1 -> v2)` comment with the old version and what 2.x expects. Search for that phrase to find them all.

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Anthropic API Key

## Setup

### Step 1: Configure the environment variables

1. Copy `.env.example` to `.env` in the project root (`cp .env.example .env`), then verify that the following variables are set correctly:

   ```bash
   ANTHROPIC_API_KEY=""  # Enter your Anthropic API secret key
   CLAUDE_MODEL=""       # Enter the Claude model ID to use
   ```

### Step 2: Install and run

This project uses [uv](https://docs.astral.sh/uv/) to manage the virtual environment and dependencies. Install uv if you don't have it (see the [installation guide](https://docs.astral.sh/uv/getting-started/installation/)), then run:

```bash
uv run main.py
```

`uv run` creates `.venv` and installs the locked dependencies from `uv.lock` on first use, so there is no need to create or activate a virtual environment yourself. To install the dependencies without running anything, use `uv sync`.

To add or remove a dependency, use `uv add <package>` or `uv remove <package>` rather than `pip install`, so that `pyproject.toml` and `uv.lock` stay in sync.

## Usage

### Basic Interaction

Simply type your message and press Enter to chat with the model.

### Document Retrieval

Use the @ symbol followed by a document ID to include document content in your query:

```text
> Tell me about @deposition.md
```

### Commands

Use the / prefix to execute commands defined in the MCP server:

```text
> /summarize deposition.md
```

Commands will auto-complete when you press Tab.

## Development

### Adding New Documents

Edit the `mcp_server.py` file to add new documents to the `docs` dictionary.

### Implementing MCP Features

To fully implement the MCP features:

1. Complete the TODOs in `mcp_server.py`
2. Implement the missing functionality in `mcp_client.py`

### Testing the MCP Server on Its Own

To try the server's tools without the chat app, open it in the MCP Inspector (requires Node.js):

```bash
uv run mcp dev mcp_server.py
```

### Linting and Typing Check

There are no lint or type checks implemented.
