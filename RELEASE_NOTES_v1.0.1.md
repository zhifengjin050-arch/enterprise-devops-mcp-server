# Enterprise DevOps MCP Server v1.0.1

## Highlights

- MCP-based AI DevOps automation for Cursor / Claude / custom Agents
- Infrastructure monitoring（Linux / Docker / Kubernetes / SSH）
- Secure execution model with enterprise controls
- Enterprise security defaults（execute off by default）

## Capabilities

| Area | Status |
|------|--------|
| System Monitoring | Included |
| Docker Management | Included |
| Kubernetes Monitoring | Included |
| SSH Remote Operations | Included |
| Permission Control | Included |
| Execute Protection | Included |
| Audit Logging | Included |
| Docker Deployment | Included |

## Testing

**225 passed**

## Deployment

- Local: `python -m app.server`
- Docker: `docker compose up -d --build`
- CI: GitHub Actions on `push` / `pull_request`

## Security Notes

- Default: `EXECUTE_TOOLS_ENABLED=false`
- Dangerous commands（e.g. `rm -rf /`）are blocked before remote execution
- Do not commit `.env`, keys, tokens, or real infrastructure identifiers

## Links

- [Changelog](CHANGELOG.md)
- [Security Architecture](docs/security.md)
- [Architecture](docs/architecture.md)
- [Contributing](CONTRIBUTING.md)
