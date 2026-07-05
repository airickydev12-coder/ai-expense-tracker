\# Engineering Notes



\## Project

AI Expense Tracker



\## Date

2026-07-01



\## Lesson 1



Today I learned:



\- How Python functions work.

\- How modules are imported.

\- Why code should be separated into different files.

\- How program flow works using a menu loop.

\- What variable scope means.

\- How to debug a NameError.



\## Challenges



\- Accidentally placed logic outside the main() function.

\- Learned that variables only exist within their scope.

\- Learned to read Python error messages.



\## Reflection



I now understand why software is organized into multiple files instead of putting everything into one script.



\# Engineering Decision Log



\---



\## EDL-001

\*\*Date:\*\* 2026-07-04



\### Title

Separate Core from Business Domains



\### Context

The project had configuration, business logic, and CLI code in the same package.



\### Decision

Create:



src/

&#x20;   core/

&#x20;   financial/



\### Why

Separate reusable infrastructure from business-specific code.



\### Alternatives Considered

Keep everything under src/



\### Consequences

Cleaner architecture.

Easier to add CRM, Healthcare, and future products.



\### Status

Accepted



\---



\## EDL-002

\*\*Date:\*\* 2026-07-05



\### Title

Expense Domain Model



\### Context

Expenses were represented as dictionaries.



\### Decision

Create an Expense dataclass and store Expense objects in memory.



\### Why

Improves readability, type safety, testing, IDE support, and future database integration.



\### Alternatives Considered

Continue using dictionaries.



\### Consequences

Serialization now occurs only in the persistence layer.



\### Status

Accepted



\---



\## EDL-003

\*\*Date:\*\* 2026-07-05



\### Title

Sequential Expense IDs



\### Context

Expenses needed stable identifiers.



\### Decision

Use sequential integer IDs that are never reused.



\### Why

Matches SQLite AUTOINCREMENT behavior.



\### Alternatives Considered

UUIDs



\### Consequences

Simple implementation today.

Easy migration to relational databases.



\### Status

Accepted





## EDL-001

### Decision
Use Expense objects instead of dictionaries.

### Reason
Improve readability and type safety.
