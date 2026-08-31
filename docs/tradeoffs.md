# Architectural trade-offs

- A modular Django monolith keeps deployment and transactions simple while
  domain boundaries remain explicit in apps. Splitting into services would add
  operational overhead before scale requires it.
- PostgreSQL is used for development-like and production-like runs so database
  behavior matches deployment. Tests use isolated SQLite for speed.
- Redis serves both Channels and Celery. This reduces infrastructure today;
  independent clusters can be introduced if traffic or reliability demands it.
- Nginx serves the immutable Vite bundle and proxies API/WebSocket traffic,
  avoiding CORS complexity for the production-like browser flow.
- `seed_demo` is deliberately deterministic and idempotent. It is a demo aid,
  not a fixture-loading mechanism for real production data.
