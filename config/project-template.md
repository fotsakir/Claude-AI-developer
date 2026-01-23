# Project Blueprint Template

Use this template with Claude Assistant to design your solution. Copy the completed blueprint to your project's description or CLAUDE.md.

---

## 1. Project Overview

**Project Name:** [Name]

**One-line Description:** [What does this project do?]

**Problem Statement:**
[What problem are you solving? Who is the target user?]

**Goals:**
- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

---

## 1.5 Existing Code (If Importing)

**Skip this section for new projects.**

### Import Source
- **Source Type:** [ZIP / Git / Local Path]
- **Source URL/Path:** [URL or path to existing code]
- **Import Mode:** [Extend (continue developing) / Reference (use as template)]

### What Exists
*After analysis, fill in:*
- **Primary Language:** [Auto-detected]
- **Framework:** [Auto-detected]
- **File Count:** [Auto-detected]
- **Entry Points:** [Auto-detected]

### What to Keep
- [ ] Database schema / migrations
- [ ] Authentication system
- [ ] API structure
- [ ] UI components
- [ ] Configuration files
- [ ] Business logic

### What to Change/Add
1. [Feature/change to add]
2. [Feature/change to add]
3. [Feature/change to add]

### Known Issues / Technical Debt
- [Issue 1]
- [Issue 2]

---

## 2. Tech Stack

### Frontend
- **Framework:** [React / Vue / Angular / Vanilla JS / None]
- **Styling:** [Tailwind / Bootstrap / CSS Modules / Styled Components]
- **State Management:** [Redux / Zustand / Context / None]
- **Build Tool:** [Vite / Webpack / None]

### Backend
- **Language:** [Python / Node.js / PHP / Go / Other]
- **Framework:** [Flask / FastAPI / Express / Laravel / None]
- **API Style:** [REST / GraphQL / None]

### Database
- **Type:** [MySQL / PostgreSQL / MongoDB / SQLite / None]
- **ORM:** [SQLAlchemy / Prisma / Eloquent / None]

### Infrastructure
- **Hosting:** [VPS / Cloud / Shared / Local]
- **Web Server:** [Nginx / Apache]
- **Other Services:** [Redis / Elasticsearch / S3 / etc.]

---

## 3. Database Schema

### Tables/Collections

```
[table_name]
├── id (PK)
├── field1 (type) - description
├── field2 (type) - description
├── created_at (datetime)
└── updated_at (datetime)

[another_table]
├── id (PK)
├── table_name_id (FK -> table_name)
└── ...
```

### Relationships
- [table1] 1:N [table2] - description
- [table2] N:M [table3] - description

---

## 4. API Endpoints

### Authentication
```
POST /api/auth/login      - User login
POST /api/auth/register   - User registration
POST /api/auth/logout     - User logout
```

### [Resource Name]
```
GET    /api/resource      - List all
GET    /api/resource/:id  - Get one
POST   /api/resource      - Create new
PUT    /api/resource/:id  - Update
DELETE /api/resource/:id  - Delete
```

---

## 5. File Structure

```
project-root/
├── frontend/              # Frontend application
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom hooks
│   │   ├── utils/         # Helper functions
│   │   └── styles/        # Global styles
│   └── public/            # Static assets
│
├── backend/               # Backend application
│   ├── app/
│   │   ├── routes/        # API routes
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   └── utils/         # Helper functions
│   └── config/            # Configuration files
│
├── database/              # Database files
│   ├── migrations/        # Schema migrations
│   └── seeds/             # Seed data
│
└── docs/                  # Documentation
```

---

## 6. Features Breakdown

### MVP (Must Have)
1. **Feature 1:** [Description]
   - Sub-task A
   - Sub-task B

2. **Feature 2:** [Description]
   - Sub-task A
   - Sub-task B

### Phase 2 (Should Have)
1. **Feature 3:** [Description]
2. **Feature 4:** [Description]

### Future (Nice to Have)
1. **Feature 5:** [Description]
2. **Feature 6:** [Description]

---

## 7. Milestones / Roadmap

### Milestone 1: Foundation
- [ ] Project setup
- [ ] Database schema
- [ ] Basic API structure
- [ ] Authentication

### Milestone 2: Core Features
- [ ] Feature 1
- [ ] Feature 2

### Milestone 3: Polish
- [ ] UI improvements
- [ ] Testing
- [ ] Documentation

---

## 8. Coding Standards

### General
- Language: [English / Greek] for code and comments
- Indentation: [2 spaces / 4 spaces / tabs]
- Max line length: [80 / 120 / none]

### Naming Conventions
- Variables: `camelCase` / `snake_case`
- Functions: `camelCase` / `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Files: `kebab-case` / `snake_case`

### Git
- Branch naming: `feature/`, `fix/`, `refactor/`
- Commit style: [Conventional Commits / Free form]

---

## 9. External Integrations

- [ ] Payment: [Stripe / PayPal / None]
- [ ] Email: [SendGrid / Mailgun / SMTP]
- [ ] Storage: [S3 / Local / Cloudinary]
- [ ] Analytics: [Google Analytics / Plausible / None]
- [ ] Other: [...]

---

## 10. Security Considerations

- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS protection
- [ ] CSRF tokens
- [ ] Rate limiting
- [ ] Password hashing
- [ ] HTTPS only
- [ ] Environment variables for secrets

---

## 11. Notes / Decisions

[Any important decisions, constraints, or notes about the project]

---

## 12. Ticket Execution Design

### Execution Order & Parallelism

CodeHero can run tickets in **parallel** within a project:
- **Max 10 projects** run simultaneously
- **Max 5 tickets per project** run in parallel (with same `sequence_order`)

### Key Concepts

| Concept | Purpose | Blocks Execution? |
|---------|---------|-------------------|
| `sequence_order` | Order + parallel grouping | **NO** - same seq runs parallel |
| `parent_ticket_id` | Context inheritance + implicit dependency | **YES** - parent must be done |
| `depends_on` | Explicit dependency | **YES** - must be done/skipped |

### Sequence Order (Parallel Groups)

Tickets with the **same `sequence_order`** run in parallel (max 5):

```
sequence_order=1: [Setup DB, Setup Config, Setup Dirs]  → run in parallel
sequence_order=2: [Create Models]                       → waits for seq 1
sequence_order=3: [API Users, API Products, API Orders] → run in parallel
sequence_order=4: [Frontend, Integration Tests]         → run in parallel
```

### Parent Tickets (Sub-tickets)

When a ticket has a `parent_ticket_id`:
- **Waits for parent** to be `done` or `skipped` (implicit dependency)
- **Gets parent context**: Summary of what parent accomplished
- **Recursive context**: Also gets grandparent, great-grandparent summaries

Use sub-tickets when:
- Breaking a feature into phases
- Follow-up tasks that need parent's results
- Maintaining context chain across related work

### Explicit Dependencies

Use `depends_on` for tickets that need another ticket's work but are NOT sub-tickets:

```
Ticket 3 (Homepage) depends_on Ticket 1 (Setup)
Ticket 3 (Homepage) depends_on Ticket 2 (Auth)
→ Homepage waits for BOTH Setup AND Auth to complete
```

### Best Practices for Parallel Work

**Rule: Parallel tickets should work on DIFFERENT files/folders**

| ✅ Good for Parallel | ❌ Bad for Parallel |
|---------------------|---------------------|
| Different pages (`/users`, `/products`) | Same component file |
| Different API endpoints | Same model file |
| Different modules/folders | Same config file |
| Independent features | Features that share state |

**Example - E-commerce Project:**

```
| Seq | Tickets (Parallel) | Files/Folders |
|-----|--------------------|---------------|
| 1 | Setup project structure | /config, /database |
| 1 | Create database schema | /migrations |
| 2 | Products API | /api/products/, /models/product.py |
| 2 | Users API | /api/users/, /models/user.py |
| 2 | Orders API | /api/orders/, /models/order.py |
| 3 | Product listing page | /pages/products/ |
| 3 | User profile page | /pages/users/ |
| 3 | Cart page | /pages/cart/ |
| 4 | Checkout flow | /pages/checkout/ (depends on cart) |
| 5 | Integration tests | /tests/ |
```

### Ticket Preview Table Format

When showing tickets to user, include:

```
| # | Ticket | Complexity | Model | Seq | Parallel | Files | Deps |
|---|--------|------------|-------|-----|----------|-------|------|
| 1 | Setup database | Simple | haiku | 1 | Yes | /database/ | - |
| 2 | Setup config | Simple | haiku | 1 | Yes | /config/ | - |
| 3 | Products API | Moderate | sonnet | 2 | Yes | /api/products/ | 1,2 |
| 4 | Users API | Moderate | sonnet | 2 | Yes | /api/users/ | 1,2 |
| 5 | Payment integration | Critical | opus | 3 | No | /services/payment/ | 3,4 |
```

**Columns:**
- **Seq**: sequence_order (same = parallel)
- **Parallel**: Yes if can run with others in same seq
- **Files**: Primary files/folders this ticket works on
- **Deps**: Dependencies by ticket number

### Sub-ticket Example

```
Parent: PROJ-0001 "Build authentication system" (seq=1)
  └── Child: PROJ-0002 "Add password reset" (seq=2, parent=PROJ-0001)
       └── Child: PROJ-0003 "Add email templates" (seq=3, parent=PROJ-0002)
```

- PROJ-0002 waits for PROJ-0001 and gets its context/summary
- PROJ-0003 waits for PROJ-0002 and gets context from BOTH PROJ-0001 and PROJ-0002

---

## Quick Start for Claude

When working on this project:
1. Follow the tech stack defined above
2. Use the file structure as guide
3. Implement features in milestone order
4. Follow coding standards
5. Always consider security
6. **Design tickets for parallel execution** where possible
7. **Separate work into different files/folders** for parallel tickets

Priority: [MVP features first / Speed / Code quality / All balanced]
