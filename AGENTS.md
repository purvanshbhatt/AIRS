# ResilAI — Agent Instructions

Please follow the ResilAI Agent Governance Protocol in `.cursorrules` and `docs/agent_memory/AGENT_START.md`.

## Codebase Knowledge Graph (graphify)

This project has an AST knowledge graph pre-indexed at `graphify-out/`.
- **Query the graph first**: For codebase questions, architectural structure, symbol lookups, or cross-file relationships, ALWAYS check `graphify-out/graph.json` first via `graphify` MCP tools (`query_graph`, `shortest_path`, `get_node`) or CLI `graphify query "<question>"`.
- **Do not scan all project files**: Never traverse or brute-force grep raw files across the entire repo when answering questions. The graph provides a scoped subgraph with exact files and line numbers in milliseconds.
- **Navigate the wiki**: If `graphify-out/wiki/index.md` exists, navigate the community articles instead of reading raw files.
- **Keep graph synchronized**: Run `graphify update .` after modifying code files to keep AST relationships up-to-date (0 API cost).

<!-- BEGIN AWS Agent Toolkit rules -->
# AWS Guidance

- Where these AWS rules conflict with the project's own instructions, the
  project's instructions take precedence.
- Prefer the AWS MCP Server for AWS interactions — it provides sandboxed
  execution, observability, and audit logging. If unavailable, use the
  AWS CLI directly.
- Before starting a task, check whether a relevant AWS skill is available.
  Load the skill with `retrieve_skill` and prefer its guidance over
  general knowledge.
- When uncertain about specific AWS details (API parameters, permissions,
  limits, error codes), verify against documentation rather than guessing.
  State uncertainty explicitly if you cannot confirm.
- When creating infrastructure, prefer infrastructure-as-code (AWS CDK or
  CloudFormation) over direct CLI commands.
- When working with infrastructure, follow AWS Well-Architected Framework
  principles.
- Do not use em dashes in AWS resource names or descriptions. Use
  hyphens instead.

## Secret Safety

- MUST load the `aws-secrets-manager` skill first for any secret,
  credential, API key, token, or password task. MUST NOT call
  `secretsmanager get-secret-value` or `batch-get-secret-value`, and MUST
  NOT hit the Secrets Manager Agent daemon directly. MUST use
  `{{resolve:secretsmanager:secret-id:SecretString:json-key}}` with
  `asm-exec` so the secret resolves at runtime without entering context.
<!-- END AWS Agent Toolkit rules -->
