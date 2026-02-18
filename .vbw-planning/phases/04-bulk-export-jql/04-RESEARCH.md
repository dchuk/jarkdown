# Phase 4: Bulk Export & JQL — Research

Gathered: 2026-02-17
Agent: Scout (haiku)

## Findings

### 1. aiohttp Best Practices for Migration from requests

**Session Management:**
- Use a single `ClientSession` instance for the application lifetime to benefit from connection pooling and cookie storage shared across all requests.
- Always use async context managers (`async with`) for session creation and cleanup.
- Multiple sessions can be created for granularity (e.g., different timeout configs), but the default is one session per application.

**Connection Pooling:**
- `TCPConnector` manages connection pooling by default. Configure:
  - `limit`: Total connection pool size (default 100)
  - `limit_per_host`: Connections per host (default 0, unlimited)
- Connector is automatically created inside `ClientSession` if not provided explicitly.

**Error Handling & Response Validation:**
- aiohttp's `ClientResponse.json()` strictly validates content-type headers and raises `ClientResponseError` if type doesn't match (more strict than requests)
- Catch `aiohttp.ClientError` and subclasses: `ClientConnectorError`, `ClientSSLError`, `ClientTimeoutError`, `ClientResponseError`
- Unlike requests, status code checks don't auto-raise; use `response.raise_for_status()` explicitly

**Timeout Configuration:**
- Use `aiohttp.ClientTimeout` with parameters: `total`, `connect`, `sock_read`, `sock_connect`
- Default total timeout is 300 seconds; explicitly set shorter values for API calls

**Graceful Shutdown:**
- After closing the session, add a small delay: `await asyncio.sleep(0.250)` for SSL connections

### 2. asyncio Patterns for CLI Tools

**Entry Points:**
- Use `asyncio.run()` as the sole entry point from synchronous CLI code
- Creates event loop, runs the main coroutine, and closes the loop automatically

**Concurrency with Semaphore:**
- `asyncio.Semaphore(n)` limits concurrent access to `n` workers
- Pattern: `async with sem: return await task_fn(*args)`
- Use `asyncio.gather(*tasks, return_exceptions=True)` for continue-and-report

**Graceful Shutdown:**
- Python 3.11+ handles SIGINT with default behavior
- For custom cleanup, attach signal handlers

### 3. Jira Cloud REST API Patterns

**Issue Search Endpoint:**
- `GET /rest/api/3/search?jql={jql_query}`
- Modern pagination (2025+): uses `nextPageToken` instead of deprecated `startAt`/`maxResults`
- Default page size: 50 issues
- Returns `nextPageToken: null` when exhausted

**Rate Limiting:**
- HTTP 429 Too Many Requests with `Retry-After` header
- Three limit types: `jira-quota-global-based`, `jira-burst-based`, `jira-per-issue-on-write`
- Response headers: `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- Best practice: double backoff delay after each successive 429

### 4. argparse Subcommand Patterns

- Parent parser with `add_help=False` for shared flags
- Child parsers inherit via `parents=[parent_parser]`
- Default subcommand: check `args.command is None` and pattern-match first arg for issue key

### 5. Attachment Downloads

- aiohttp supports streaming downloads via `response.content.read(chunk_size)`
- Share semaphore between issue fetching and attachment downloads for simplicity

## Relevant Patterns

### Async Context Manager for API Client
```python
class AsyncJiraApiClient:
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            auth=self.auth,
            connector=aiohttp.TCPConnector(limit_per_host=5)
        )
        return self

    async def __aexit__(self, *args):
        await self.session.close()
        await asyncio.sleep(0.250)
```

### Semaphore-Limited Bulk Export
```python
async def export_issues_bulk(api_client, issue_keys, semaphore):
    tasks = [api_client.fetch_issue(key, semaphore) for key in issue_keys]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]
    return successes, failures
```

### JQL Pagination with nextPageToken
```python
async def search_jql(api_client, jql_query, max_results=50):
    issues = []
    next_page_token = None
    while len(issues) < max_results:
        params = {'jql': jql_query, 'maxResults': 50}
        if next_page_token:
            params['nextPageToken'] = next_page_token
        data = await api_client.search(params)
        issues.extend(data['issues'])
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break
    return issues[:max_results]
```

## Risks

**High Priority:**
1. Semaphore + connector mismatch: If semaphore allows more concurrent tasks than `limit_per_host`, tasks queue on the connector. Set `limit_per_host >= semaphore_limit`.
2. Rate limit retry not coupled with semaphore: Must implement exponential backoff within semaphore context.
3. Strict JSON validation in aiohttp: Add explicit `Accept: application/json` headers.

**Medium Priority:**
4. nextPageToken requires sequential pagination: Cannot parallelize JQL search across pages.
5. Event loop blocking: File writes in markdown_converter must not block the loop. Use `asyncio.to_thread()` or batch writes.
6. Session lifecycle in tests: Tests must properly close sessions.

**Low Priority:**
7. SSL cleanup timing: `await asyncio.sleep(0.250)` after session close for SSL.
8. Default subcommand detection: Pattern matching on first arg is fragile; use strict regex `^[A-Z]+-\d+$`.

## Recommendations

1. Set `limit_per_host = semaphore_limit` on TCPConnector to prevent queueing bottlenecks.
2. Create a dedicated retry helper with exponential backoff respecting `Retry-After` headers.
3. Implement `__aenter__/__aexit__` on API client for session lifecycle management.
4. Use stricter issue key regex `^[A-Z]+-\d+$` for default subcommand detection.
5. Progress reporting via simple stderr counter: `print(f"\rExporting {i+1}/{total}...", end='', file=sys.stderr)`.
6. Generate index.md after all exports complete with columns: Key, Summary, Status, Type, Assignee, Result.
7. Support both `startAt`/`maxResults` (v2) and `nextPageToken` (v3) pagination for API version flexibility.
