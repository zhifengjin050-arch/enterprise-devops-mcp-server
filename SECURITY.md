# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |

## Reporting a Vulnerability

Do **not** open a public GitHub Issue for security vulnerabilities.

Report privately via GitHub Security Advisories on this repository, or contact
the maintainer through the GitHub profile.

Include:

- Affected version and commit
- Reproduction steps (no exploit payload)
- Impact assessment

## Defaults

This server is **read-only by default**.

```env
EXECUTE_TOOLS_ENABLED=false
```

Never commit `.env` files, SSH private keys, kubeconfig, or production tokens.
Use `.env.example` as the template.

Full model: [docs/security.md](docs/security.md)
