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



EDL-004



Title: Introduce Repository Pattern



Document:



Why persistence was moved out of the business layer.

Benefits for future database migration.



EDL-005



Title: Business Layer Independent of Presentation



Document:



Why input() and print() belong in the CLI.

Why business functions now accept parameters and return values instead.



These decisions capture an important shift in the architecture and will be valuable reference points as the project grows.



EDL-006 — Safe Collection Modification



Decision: Use enumerate() with pop(index) when removing an item during iteration.



Rationale:



Avoids modifying a collection through the iterator.

Makes the removal operation explicit.

Eliminates common static-analysis warnings.

Improves maintainability and clarity.

Provides direct access to the element index if future enhancements require it.



EDL-007 — Separate Presentation Package



Decision: Move the CLI into a dedicated presentation package.



Rationale:



The CLI is one implementation of the presentation layer.

Future interfaces (REST API, React frontend, desktop GUI, mobile app) belong alongside it.

Keeps the project organized according to layered architecture.

Reinforces the separation between presentation, business logic, and persistence.



EDL-008 – One Domain Concept, One Model



Every important financial concept (Expense, Budget, Account, Goal, Transaction, etc.) should be represented by its own domain model rather than generic dictionaries. This improves clarity, validation, and extensibility as the application grows.



This principle will serve you well as the project expands into accounts, goals, investments, and AI-driven financial planning.

