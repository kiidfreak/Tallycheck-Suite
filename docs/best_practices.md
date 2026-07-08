# Software Engineering Best Practices

### April 2026

## Table of Contents

1. Principles and Engineering Foundations.
   - 1.1. Human-Centric AI Accountability.
   - 1.2. Foundational Design Principles (SOLID, DRY, KISS)
   - 1.3. Naming Conventions & Code Style
   - 1.4. Dependency Management
2. Development Workflow and Collaboration.
   - 2.1. Agile Scrum Rhythm...
   - 2.2. Version Control & Branching (GitHub Flow)
   - 2.3. Commit Message Standards (Conventional Commits)
   - 2.4. The Atomic Pull Request
   - 2.5. Peer Review Rigor
   - 2.6. Code Review Etiquette..
3. Quality, Testing and Delivery.
   - 3.1. The Testing Pyramid..
   - 3.2. CI/CD Pipeline Standards.
4. Security.
   - 4.1. Zero-Trust Account Management
   - 4.2. Data Integrity & Authorization.
   - 4.3. Secrets & Environment Management
   - 4.4. Dependency Vulnerability Scanning..
5. Monitoring..
   - 5.1. Structured Logging & Observability.
   - 5.2. Error Handling Standards.
   - 5.3. Incident Response & Blameless Postmortems
6. Architecture and Documentation.
   - 6.1. Technical Debt Management
   - 6.2 Architecture Decision Records (ADR)
   - 6.3 The "Rule of Three" README.
   - 6.4 Inline Documentation Standards.

# Software Engineering Best Practices Guidelines

## 1.Principles and Engineering Foundations

This section outlines the core principles and engineering standards that guide the design and development of maintainable, scalable, and reliable software. It
establishes the foundation for consistent coding practices and long-term system sustainability.

### 1.1 Human-Centric AI

#### Accountability

Use AI as an accelerator, not an author. **You are the owner of every line of code committed.**

Automated tools (Copilot, ChatGPT, Claude) can generate code faster than humans, but they lack context and accountability. If a line of code is in the repository, you must be able to explain its logic, performance impact, and security implications as if you wrote it from scratch.

**Example:**

- **Acceptable:** Generating a complex SQL query via LLM, verifying its execution plan, and commenting the logic.

- **Unacceptable:** Committing a script that you "think" works but cannot debug if it fails.

**Reference:** ISO/IEC 25010 (Maintainability & Functional Suitability)

### 1.2 Foundational Design Principles (SOLID, DRY, KISS)

Maintainable code is a non-negotiable standard for enterprise software. We adhere to industry established patterns:

- **SOLID:** Ensures class-level stability and extension. Ensure each class has a single reason to change, remains open for extension but closed for modification, ensure child classes can be substituted for their parent classes, each class should depend only on methods that it uses, and finally higher level modules should not depend on low level ones.

- **DRY (Don't Repeat Yourself):** Minimizes logic fragmentation. If you find yourself copying the same logic into a second location, extract it into a shared utility or service.

- **KISS (Keep It Simple,Stupid):** Prioritizes readability over cleverness. A junior developer should be able to read your code and understand its intent without requiring a walkthrough.

**Example:** Refactoring a large, complex module into smaller, single-responsibility services, each handling one concern.

### 1.3 Naming Conventions & Code Style

Consistency is a feature. Inconsistency is a bug. We enforce naming conventions and automated formatting across the entire codebase.

**Naming Policy:** We use **snake_case** for all variables, functions, methods, and files. No other casing styles are permitted.

**Enforcement:** Automated formatting and linting must be enabled. "Format-on-save" is mandatory in all IDEs.

```bash
# Acceptable
user_profile = {
  first_name: 'John',
  last_name: 'Doe',
  email: [EMAIL_ADDRESS]
};

# Unacceptable
userProfile = {
  firstName: 'John',
  lastName: 'Doe',
  email: [EMAIL_ADDRESS]
};
```

### 1.4 Dependency Management

Every dependency is a liability. Treat it like one. Third-party packages introduce risk - security vulnerabilities, breaking changes, and abandoned maintenance. We do not add dependencies casually.

Adding a new package requires justification in the PR description. Consider: Is this maintained? Is it open source? Is there a lighter alternative?

**Auditing:** Run automated dependency scans weekly. Critical/High findings must be resolved within 72 hours.

**Updating:** Dependency updates are a standing item in Sprint Planning. Use tools like automated update bots to manage PRs for outdated packages.

**Lock files:** Lock files are always committed. Never run an install without reviewing the diff to the lock file. Example: Before adding a date-formatting library, check if the native built-in APIs already cover the use case.

**Reference:** OWASP SAMM (Implementation - Secure Build) | ISO/IEC 25010 (Security - Integrity)

## 2. Development Workflow and Collaboration

This section outlines the processes, tools, and collaboration practices that enable efficient teamwork and structured software development. It covers version control, code reviews, and workflows that ensure consistency and accountability across the development lifecycle.

### 2.1 Agile Scrum Rhythm

Predictable delivery via high-frequency feedback loops. We do not work in isolation. Our schedule ensures business alignment and rapid pivot capability.

- **The Monday Kick-off:** 09:00 - Sprint Planning. Review the backlog, estimate effort, and commit to the week's goals. This is also the Sprint Review window - demos of last week's completed work happen here.

- **The Daily Sync:** Pull the latest code every morning at 09:00. Resolve conflicts early, not the night before a release.

- **The Daily Sprint:** Commit to a specific, small deliverable in the morning and ensure it is code-complete and pushed by the end of the day.

- **The Wednesday Release:** Production deployments occur every Wednesday to ensure stability before the weekend. Features must be code-complete by Tuesday EOD to qualify for the release window.

**_Example:_** Moving a "Task Update" feature from 'In Progress' to 'Done' by Tuesday EOD to meet the Wednesday release window. If it misses Tuesday, it rolls to the following Wednesday.

### 2.2 Version Control & Branching (GitHub Flow)

**A clean history is a readable history.**

We use a short-lived branching strategy. Long-lived feature branches are prohibited - they create merge debt and hide integration issues.

- **Main Branch:** Production-ready code. Always deployable.

- **Staging Branch:** Lives in the office server and serves (no pun intended) as a similar environment to the production environment.

- **Dev branch:** For daily development.

- **Feature Branches:** Short-lived (feat/user_auth), branched from dev, merged via PR. Branch is closed after merge.

#### Naming Convention:

feat/, fix/, chore/, test/ prefixes are mandatory.

**Example:** git checkout -b feat/add_media_upload

**Commit Message Standards (Conventional Commits)**

**Every commit tells a story.** Make it a clear one. We follow the Conventional Commits specification. This enables automated changelogs, semantic versioning, and makes git log useful for debugging.

**Example:**

```bash
feat(auth): add user login endpoint
fix(media): update image upload component
chore(deps): update dependencies
```

- **Types**: feat, fix, chore, docs, refactor, test, style, perf
- **Scope**: The module or component affected (e.g., auth, media, api)

**Reference**: IEEE 828 (Configuration Management - Change Documentation) | Conventional Commits v1.0.0

### 2.3 The Atomic Pull Request

Small changes are safe changes. PRs over 200 lines suffer from **_reviewer fatigue_** - studies show review quality drops dramatically after 400 lines. We break large features into functional slivers that can be reviewed, tested, and rolled back independently.

**_Example:_** Instead of "Refactor Entire Auth System,"
create:

- **PR #1:** Update User
  Interface Definitions (20 lines).

- **PR #2:** Implement Auth
  Implementation logic (50 lines).

- **PR #3:** Update Login View
  (100 lines).

### 2.4 Peer Review Rigor

Approvals are a signature of quality. **Every PR requires 1+ reviewer.** Reviewers must verify
the following before approving:

- **Correctness:** Does this solve the task/issue?

- **Readability:** Can I understand this without the author explaining it?

- **Safety:** Does it handle nulls, errors, and edge cases?

- **Patterns:** Does it follow our existing style and architecture?

## 2.5 Code Review Etiquette

Review the code, not the coder. Code review is a collaborative process, not an adversarial one. **The goal is to improve the code and share knowledge**, not to prove superiority.

- **Be constructive:** Never say "this is wrong" without suggesting an alternative. Frame feedback as questions when possible: "Have you considered using X here?"

- **Be timely:** Respond to review requests within 24 hours. Blocking a teammate's PR for days is blocking the team's velocity.

- **Be specific:** "This could be improved" is useless. "This logic could be replaced with a more efficient approach - here's how" is actionable.

- **Acknowledge good work:** If a solution is elegant, say so. Positive reinforcement builds a healthy review culture. Example:

**Example**

```python
# Poor Example:
This is bad. I don't like this.
```

```python
# Constructive Example:
This works but we could simplify this and make it more readable by using the existing AuthService.validateToken() method instead of re-implementing the logic here.
```

## 3. Quality, Testing and Delivery

This section outlines the strategies used to ensure software quality, reliability, and smooth delivery. It highlights testing approaches and pipeline practices that support continuous integration and stable releases.

### 3.1 The Testing Pyramid

Automated verification at every level. No code is "Done" until it is verified. We follow the testing pyramid to balance speed and confidence:

- **Unit Tests (70%):** Fast, isolated tests for logic. Every public method in a service gets at least one positive and one negative test case.

- **Integration Tests (20%):** Verifying service-to-service communication, database queries, and API endpoint behaviour with realistic data.

- **E2E/Manual (10%):** Final verification of the user journey.

**Example:** Adding a unit test file alongside every new service method. The test file verifies the happy path, error handling, and edge cases (e.g., empty input, null responses).

Reference: ISO/IEC 29119 (Software Testing Standards)

## 3.2 CI/CD Pipeline Standards

If it is not automated, it is not enforced. The CI/CD pipeline is the enforcement mechanism. No code reaches dev from your branch without passing through automated gates.

- **Gate 1 - Lint:** Code must pass lint tests with zero errors.

- **Gate 2 - Build:** The project must compile successfully in both Debug and Release configurations.

- **Gate 3 - Test:** All unit tests must pass. A failing test blocks the merge.

- **Gate 4 - Security Scan:** Automated dependency vulnerability scanning must report no critical/high findings.

**Example:** A PR that passes code review but fails the lint gate cannot be merged. The developer must fix the lint issues before re-requesting review.

Reference: ISO/IEC 12207 (Quality Assurance Process) | OWASP SAMM (Implementation - Build & Deploy)

## 4. Security

This section outlines the security practices and controls required to safeguard systems, data, and dependencies. It emphasizes proactive risk management, secure access, and protection against vulnerabilities throughout the development process.

### 4.1 Zero-Trust Account Management

Absolute isolation of personal and professional identities. Use of personal accounts for company work is a breach of policy. Personal accounts create audit trail gaps, license compliance issues, and data leakage vectors.

**Example**: Authenticate all tools (GitHub, sync, cloud providers, package managers) using your company identity only. Personal SSH keys must not be used for company repositories.

Reference: OWASP SAMM (Governance - Security Awareness)

### 4.2 Data Integrity & Authorization

No data access without explicit scope validation. We prioritize "Security by Design."

API endpoints must be guarded by robust auth logic. Every endpoint (unless it's public e.g. /health, /login, /register) must explicitly declare its authorization requirements.

**Example**: Using centralized mechanisms to inject authorization tokens and authorization guards on all sensitive endpoints. Checking ownership or scope on every data query, not just at the controller level.

```python
# Incorrect - trusts the caller implicitly
@app.route('/users/<username>')
def get_user(username):
    # Trusts caller knows username
    user = db.get_user(username)
    # ...
```

```python
# Correct - validates at the gate
@app.route('/users/<username>')
@requires_auth
def get_user(username):
    if username != get_current_user():
        raise PermissionError("Cannot access someone else's data")
    user = db.get_user(username)
    # ...
```

Reference: OWASP Top 10 (A01: Broken Access Control) | ISO/IEC 25010 (Security)

### 4.3 Secrets & Environment Management

Secrets belong in vaults, never in code. Hardcoded API keys, connection strings, and credentials in source code are a critical vulnerability. Secrets must be externalized and managed through secure channels.

**Local development**: Use environment files that are listed in .gitignore. Never commit these files.

**CI/CD & Production**: Use **GitHub Actions** for all secret management and environment variables.

**Rotation**: Secrets must be rotated on a defined schedule and immediately upon any suspected compromise.

```python
# Incorrect
DATABASE_URL="postgresql://user:password@host:1234/database"
```

```python
# Correct
DATABASE_URL="postgresql://[DB_USER]:[DB_PASSWORD]@[DB_HOST]:[DB_PORT]/[DB_NAME]"

# .env file - only for local development
# Never commit .env files to version control. Put in .gitignore
DB_USER="user"
DB_PASSWORD="password"
DB_HOST="host"
DB_PORT="1234"
DB_NAME="database"
```

**Reference:** OWASP Top 10 (A07: Security Misconfiguration) | OWASP SAMM (Implementation - Secure Build)

### 4.4 Dependency Vulnerability Scanning

Your code is only as secure as your weakest dependency. Third-party packages are the most common attack vector in modern software. We run automated vulnerability scans as part of our CI/CD pipeline and as a manual weekly check.

**Vulnerability Scans:** Both frontend and backend auditing tools must report zero critical/high vulnerabilities.

**Automated Alerts:** Automated bots must be enabled on all repositories to flag outdated or vulnerable packages.

**Example:** A high-severity vulnerability flagged by an audit must be patched or the affected module replaced within 48 hours of discovery.

**Reference:** OWASP Top 10 (A06: Vulnerable and Outdated Components) | OWASP SAMM (Verification - Security Testing)

### 5.1 Structured Logging & Observability

This section outlines the mechanisms used to observe system performance, detect issues, and respond to failures. It focuses on logging, error handling, and incident response to ensure system reliability and operational stability.

If you cannot observe it, you cannot fix it. When production breaks, logs are your only witness.

We use structured logging (JSON format) with consistent severity levels, so logs are searchable, filterable, and actionable.

**Severity Levels:**

**DEBUG** (local only)

**INFO** (routine operations)

**WARN** (recoverable issues)

**ERROR** (failures requiring attention)

**FATAL** (system-down events).

**Context:** Every log entry must include a correlation ID, timestamp, user context (where applicable), and the operation being performed.

**What NOT to log:** Passwords, tokens, PII (personally identifiable information), or full request/response bodies containing sensitive data. Example:

```python
# Bad - Logging sensitive data
logger.info(f"User {user.id} logged in with password {user.password}")  # ❌ Never do this
logger.info(f"API response: {json.dumps(response_body)}")  # ❌ Never log full bodies

# Good - Logging only what's necessary
logger.info(f"User {user.id} logged in successfully", extra={
    "ip_address": user.last_login_ip,
    "user_agent": request.headers.get('User-Agent')
})
logger.info("Login successful", extra={
    "user_id": user.id,
    "ip_address": request.remote_addr
})
```

### 5.2 Error Handling Standards

**Fail gracefully. Recover automatically. Escalate intentionally.**

Unhandled exceptions are unacceptable in production. Every external call (database, API, file system) must be wrapped in appropriate error handling with clear recovery or escalation paths.

**API layer:** Return standardized error responses. Never expose internal stack traces to the client.

**Client side:** Display user-friendly error messages. Log the technical details to a monitoring service.

**Retry logic:** Transient failures (network timeouts, 503s) should be retried with exponential backoff before escalating. Example:

```python
# Bad - Not handling exceptions
def get_external_data(url):
   response = requests.get(url)  # Might raise network error
   return response.json()  # Might raise JSON decode error
```

```python
# Good - Handling exceptions
@retry(
   stop=stop_after_attempt(3), # Limit to 3 retries
   wait=exponential_jitter(initial=1, max=10) # Exponential backoff with jitter
   )
def get_external_data(url):
   try:
      response = requests.get(url, timeout=10)  # Added timeout
      response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses
      return response.json()  # Handle JSON decode error
   except requests.exceptions.RequestException as e:
      logger.error(f"Failed to fetch data from {url}: {e}")
      raise
   except json.JSONDecodeError as e:
      logger.error(f"Failed to decode JSON from {url}: {e}")
      raise
```

### 5.3 Incident Response & Blameless Postmortems

**Every outage is a learning opportunity, not a blame opportunity.** When production incidents occur, we follow a structured response process:

- **Detect:** Monitoring/alerting triggers or a user report surfaces the issue.

- **Triage:** Determine severity (P1-Critical, P2-High, P3-Medium, P4-Low) and assign an incident lead.

- **Mitigate:** Restore service first. Roll back the offending deployment if necessary. Do not attempt a "fix-forward" under pressure.

- **Resolve:** Once stable, apply the proper fix through the normal PR process.

- **Review:** Conduct a blameless postmortem within 48 hours.

**Postmortem Template:**

- **What happened?** (Timeline of events)

- **What was the impact?** (Users affected, duration)

- **What was the root cause?**

- **What are the action items to prevent recurrence?**

**Example:** A deployment causes an error on an endpoint. The team rolls back within 15 minutes, then schedules a postmortem for the following morning.

**Reference:** OWASP SAMM (Operations - Incident Management) | ISO/IEC 12207 (Problem Resolution Process)

## 6. Architecture and Documentation

This section outlines the standards for managing system design, documenting key
decisions, and maintaining clarity in technical communication. It supports
**long-term maintainability, knowledge sharing, and effective system evolution.**

### 6.1 Technical Debt Management

Acknowledge it. Track it. Pay it down systematically. Technical debt is inevitable, but unmanaged technical debt is a project killer. We track it explicitly and allocate time to reduce it.

**Identification:** Use `// TODO:` and `// HACK:` comments in code, linked to an entry in that project's management sheet. Naked TODOs without a reference are not permitted.

**Tracking:** Technical debt items live in the project's management sheet alongside feature work, tagged with a tech-debt label.

**Allocation:** A minimum of 20% of each sprint's capacity is reserved for tech debt reduction and refactoring. This is non-negotiable.

```python
# Bad
# TODO: Remove this temporary fix
def process_order(order):
   pass
```

```python
# Good
# TODO(No. 128): Remove this temporary fix when the payment gateway is stable
def process_order(order):
   pass
```

### 6.2 Architecture Decision Records (ADR)

Document the **_"Why"_** not just the **_"How."_**

When we make a significant architectural choice, we record the rationale, so future developers understand the context - even if those future developers are us.

**Example:** A documentation file explaining why we chose a specific storage provider over alternatives, including the considered options and trade-offs.

**Reference:** IEEE 1016 (Software Design Descriptions)

### 6.3 The "Rule of Three" README

Every repo must be deployable by a new hire in 5 minutes. Every project must contain a README with:

- **Setup:** How to run locally (prerequisites, install steps, environment variables).

- **Testing:** How to run the test suite and what to expect.

- **Architecture:** High-level overview of the project structure, key directories, and how the pieces connect.

**Example:** A new developer clones the repo, reads the README, and has the application running locally within five minutes. If they cannot, the README is incomplete.

### 6.4 Inline Documentation Standards

Code must be explicitly documented. We do not require comments on every line. We require comments on every decision that isn't obvious from the code itself.

- **Public APIs:** All public methods and data structures must have documentation comments describing parameters, return values, and exceptions.

- **Complex logic:** Any algorithm, workaround, or non-obvious business rule must have a comment explaining _why_, not _what_.

- **No commented-out code:** Dead code must be deleted, not commented out. Git is the archive.

```python
# Bad
# This function processes an order
def process_order(order):
#    pass
```

```python
# Good
# 'order' parameter is processed only after all validations are passed
# because without it we can have invalid orders in the system
def process_order(order):
   pass


```

**Reference:** ISO/IEC 25010 (Maintainability - Analysability)
