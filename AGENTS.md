# Repository Guidelines

## Project Structure & Module Organization

DeerFlow pairs a Python LangGraph backend with a Next.js interface. Core runtime lives in `src/`, especially `agents/`, `graph/`, `server/`, `tools/`, and `workflow.py`, while `config/`, `prompt_enhancer/`, `rag/`, and `utils/` supply shared services. Backend tests reside in `tests/`; sample workflows and assets live in `examples/` and `assets/`. The `web/` directory holds the UI, with deployment aids in `Dockerfile`, `docker-compose.yml`, and `bootstrap.*`. Copy `.env.example` and `conf.yaml.example`, and consult `docs/` before changing runtime behaviour.

## Build, Test, and Development Commands

Install backend dependencies with `uv sync`, or `make install-dev` to include linting and test extras. Start the FastAPI/LangGraph service via `make serve` (`uv run server.py --reload`). Format and lint using `make format` and `make lint`. Run the full backend test suite with `make test`; gather coverage through `make coverage`. For the UI, enter `web/` and execute `pnpm install`, `pnpm dev` for local development, and `pnpm build` when validating production output. `make lint-frontend` wraps the lint, type-check, and build checks.

## Coding Style & Naming Conventions

Target Python 3.12, four-space indentation, and Ruff's 88-character line length. Prefer `snake_case` for modules and functions, `PascalCase` for classes, and descriptive LangGraph node IDs (e.g., `research_router`). Use concise docstrings for non-obvious graph steps. Apply `uv run ruff format` before committing; `ruff check --fix --select I` enforces import ordering and lint rules. Frontend code follows Next.js conventions with Prettier (`pnpm format:write`) and TypeScript strictness, mirroring existing component layouts.

## Testing Guidelines

Pytest discovers files in `tests/` that match `test_*.py`; lean on `pytest-asyncio` fixtures when exercising graph execution. Coverage defaults to `--cov=src` with a 25% threshold, so extend suites whenever you touch `src/`. Use `uv run pytest -k <pattern>` for focused runs, and surface reusable payloads in `examples/`. UI changes should pass `pnpm lint` and `pnpm typecheck`; add co-located component tests when introducing interactive behaviour.

## Commit & Pull Request Guidelines

Follow the conventional prefixes visible in `git log` (e.g., `fix: <scope> (#123)` or `feat: <scope>`). Keep commits narrow, including schema or config updates alongside the code that depends on them, and avoid committing generated artefacts. Pull requests need a problem statement, summary of changes, config or migration notes, and references to issues. Attach screenshots or GIFs for UI work and list the validation commands you ran.

## Configuration & Security Tips

Never commit populated `.env` or `conf.yaml`; duplicate the provided examples and inject keys locally. Sensitive integrations live under `tools/` and `rag/`, so gate new ones behind environment variables and document them in `docs/configuration_guide.md`. Update `conf.yaml.example` and add release notes whenever you introduce required settings.

## Project Overview & Architecture

 📊 Execution Summary

- 14 claude.md files generated across the entire project
- Root documentation: Comprehensive project overview with navigation
- Directory-level docs: Detailed analysis of each major component
- Navigation index: Complete feature mapping and cross-references

  🏗️ Architecture Mapped

- Core workflow engine (src/graph/) - LangGraph state management
- Multi-agent system (src/agents/) - Intelligent collaboration
- Tool ecosystem (src/tools/) - Search, crawl, code execution
- Configuration management (src/config/) - System settings and env vars
- LLM abstraction layer (src/llms/) - Multi-provider support
- Prompt system (src/prompts/) - Role-based templates
- RAG components (src/rag/) - Vector database integration
- API services (src/server/) - FastAPI endpoints
- Extension modules (src/podcast/, src/ppt/, src/prose/) - Specialized features
- Testing framework (tests/) - Unit and integration tests
- Web frontend (web/) - Next.js user interface

  🎯 Key Benefits Created

  1. Rapid onboarding: New developers can understand the project in minutes
  2. Intelligent navigation: Find code by concept, not just file paths
  3. Context preservation: Maintain understanding across sessions
  4. Precise problem-solving: Quickly locate relevant code sections
  5. Architectural understanding: Grasp system design patterns instantly

  📚 Documentation Structure

  deer-flow/
  ├── claude.md              # Root project overview
  ├── NAVIGATION.md          # Complete feature map
  ├── src/
  │   ├── agents/claude.md   # Agent system documentation
  │   ├── config/claude.md   # Configuration management
  │   ├── graph/claude.md    # Workflow engine
  │   ├── tools/claude.md    # Tool integration
  │   ├── llms/claude.md     # LLM abstraction
  │   ├── prompts/claude.md  # Prompt templates
  │   ├── rag/claude.md      # RAG system
  │   ├── server/claude.md   # API services
  │   ├── podcast/claude.md  # Audio generation
  │   ├── ppt/claude.md      # Presentation generation
  │   └── prose/claude.md    # Text processing
  ├── tests/claude.md        # Testing framework
  └── web/claude.md          # Frontend application
