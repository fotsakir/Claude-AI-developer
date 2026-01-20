# TODO: Project Import & Smart Context Enhancement

## Date: 2026-01-20

---

## ΟΛΟΚΛΗΡΩΘΗΚΑΝ

### 1. AI Model Selection για Project Planner
- **MCP tools ενημερώθηκαν** με `ai_model` parameter:
  - `codehero_create_project` - ai_model (opus/sonnet/haiku)
  - `codehero_create_ticket` - ai_model per ticket
  - `codehero_bulk_create_tickets` - ai_model per ticket
  - `codehero_update_ticket` - αλλαγή ai_model
  - `codehero_get_project_progress` - δείχνει model_distribution + tickets list

- **Ροή Project Planner:**
  1. Ρώτα: "Σταθερό ή δυναμικό μοντέλο;"
  2. Αν δυναμικό: "eco / balanced / performance;"
  3. Δείξε preview table με tickets + models
  4. Ζήτα επιβεβαίωση πριν δημιουργήσεις

- **Στρατηγικές:**
  - `eco` - Προτιμά haiku, sonnet για moderate, opus μόνο για critical
  - `balanced` - Ανάλογα πολυπλοκότητα (DEFAULT)
  - `performance` - Προτιμά opus/sonnet

- **Developer Roles:**
  - Opus = Master Developer
  - Sonnet = Senior Developer
  - Haiku = Junior Developer

- **CLAUDE.md ενημερώθηκε** με οδηγίες

### 2. Smart Context - Language Detection Fix
- **smart_context.py ενημερώθηκε** για να αναγνωρίζει:
  - C, C++, C#, Java, Kotlin, Go, Rust, Swift, Objective-C
  - Python, PHP, Ruby, Perl, Lua
  - JavaScript, TypeScript, React, Vue, Svelte
  - HTML, CSS, SCSS, Dart, Shell, SQL, Scala, Elixir, Haskell, R

- **Entry points** τώρα βρίσκει:
  - index.html, index.php, main.py, main.c, main.cpp
  - Program.cs, Main.java, main.go, main.rs, main.dart, etc.

- **Tech stack detection** για:
  - Laravel, Symfony, Django, Flask, FastAPI, Spring Boot
  - .NET, ASP.NET Core, React, Vue, Angular, Next.js
  - Docker, CMake, Cargo, Maven, Gradle, Flutter, Rails

---

## ΜΕΝΕΙ ΝΑ ΓΙΝΕΙ

### 3. Project Import Feature

**Σκοπός:** Να μπορεί ο χρήστης να εισάγει υπάρχον project στο CodeHero

**3 τρόποι εισαγωγής:**
1. **ZIP αρχείο** - Upload & extract
2. **Git clone** - `git clone URL`
3. **Τοπικός φάκελος** - "Πάρε το από /path/to/project" (για τεράστια projects)

**2 σενάρια χρήσης:**

#### Σενάριο A: Επέκταση Project
```
Χρήστης: "Θέλω να συνεχίσω αυτό το project"

1. Upload (ZIP/git/path) → /var/www/projects/{project}/
2. Analysis & Indexing → Smart Context tables
3. Δημιουργία "map" για να ξέρει το AI πού είναι τι
4. Tickets για επέκταση (χωρίς να πειράζει το υπάρχον)

Στόχος: Αποδοτικό AI, λίγα tokens, ξέρει τι υπάρχει
```

#### Σενάριο B: Reference Project
```
Χρήστης: "Θέλω να φτιάξω κάτι σαν αυτό"

1. Upload → /opt/codehero/references/{project}/ (ξεχωριστά)
2. Analysis → Κατανόηση δομής & λειτουργιών
3. Ερωτήσεις στον χρήστη: "Τι θέλεις να κρατήσεις;"
4. Νέο κενό project + tickets με βάση τις προδιαγραφές

Το reference μένει αποθηκευμένο για να το ψάξει αν χρειαστεί
```

### 4. MCP Tools για Import

**Νέα tools που χρειάζονται:**

```python
codehero_import_project(
    source_type: "zip" | "git" | "path",
    source: str,  # URL, path, or zip content
    project_id: int,  # Existing project to import into
    mode: "extend" | "reference"  # Extend project or use as reference
)

codehero_analyze_project(
    project_id: int,
    force: bool = False  # Re-analyze even if map exists
)
```

### 5. Analysis Layers (για μεγάλα projects)

```
Layer 1: Structure Map
  - Φάκελοι & αρχεία (tree)
  - Μέγεθος αρχείων
  - Τελευταία τροποποίηση

Layer 2: Tech Detection
  - Tech stack (PHP, Node, Python, etc)
  - Framework (Laravel, Express, Django, etc)
  - Dependencies (composer.json, package.json, etc)

Layer 3: Code Mapping
  - Entry points (index.php, app.js, main.py)
  - Routes/endpoints
  - Models/entities
  - Key functions & classes

Layer 4: Pattern Recognition (για κακογραμμένα projects)
  - Auth system
  - Database access pattern
  - API structure
  - Config management
```

### 6. Reference Storage

**Νέος φάκελος:**
```
/opt/codehero/references/{project_code}/
```

**ΣΗΜΑΝΤΙΚΟ: Πρέπει να προστεθεί στο setup script!**

```bash
# Στο install.sh ή setup.sh
sudo mkdir -p /opt/codehero/references
sudo chown -R claude:claude /opt/codehero/references
sudo chmod 755 /opt/codehero/references
```

**Αρχεία setup που πρέπει να ενημερωθούν:**
- `install.sh` - Fresh installation
- `upgrade.sh` - Upgrade existing installation (να δημιουργεί αν δεν υπάρχει)

**Νέο πεδίο στη βάση (ή νέος πίνακας):**
```sql
-- Option A: Νέο πεδίο στο projects
ALTER TABLE projects ADD COLUMN reference_path VARCHAR(500);

-- Option B: Νέος πίνακας
CREATE TABLE project_references (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    reference_name VARCHAR(255),
    reference_path VARCHAR(500),
    analyzed_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

### 7. Οδηγίες σε ΠΟΛΛΑ σημεία

**ΣΗΜΑΝΤΙΚΟ:** Οι οδηγίες πρέπει να μπουν σε 4 σημεία:

#### A. Claude Assistant (`/home/claude/CLAUDE.md`)
- Γενικές οδηγίες για import projects
- Πώς να ρωτάει extend vs reference
- Πώς να χειρίζεται μεγάλα projects

#### B. Project Planner Templates (3 templates)
- Template 1: Web projects
- Template 2: App projects
- Template 3: API projects
- Κάθε template πρέπει να ξέρει πώς να χειρίζεται imported code

#### C. AI των Tickets (daemon system prompt)
- Πώς να χρησιμοποιεί το project_map
- Πώς να χρησιμοποιεί τα reference projects
- Πώς να μην σπαταλάει tokens σε exploration

#### D. Smart Context injection
- Το project_map πηγαίνει αυτόματα στο AI
- Το reference project info πρέπει επίσης να πηγαίνει

---

## ΥΠΑΡΧΟΝΤΑ TABLES (Smart Context)

Ήδη υπάρχουν στη βάση `claude_knowledge`:

| Table | Σκοπός |
|-------|--------|
| `project_maps` | Structure, tech stack, entry points |
| `project_knowledge` | Learned patterns, gotchas, decisions |
| `user_preferences` | User settings |
| `conversation_extractions` | Compressed old conversations |

---

## ΣΗΜΕΙΩΣΕΙΣ

1. Η βάση είναι `claude_knowledge` (όχι codehero)
2. Ο daemon ήδη καλεί `build_full_context()` για κάθε ticket
3. Το smart_context.py τρέχει αυτόματα κατά τη δημιουργία ticket
4. Τα παλιά projects χρειάζονται manual re-analyze

---

## ΑΡΧΕΙΑ ΠΟΥ ΠΡΕΠΕΙ ΝΑ ΕΝΗΜΕΡΩΘΟΥΝ

| Αρχείο | Τοποθεσία | Σκοπός |
|--------|-----------|--------|
| CLAUDE.md | `/home/claude/CLAUDE.md` | Claude Assistant οδηγίες |
| project-template.md | `/home/claude/codehero/config/project-template.md` | Project blueprint template |
| claude-daemon.py | `/home/claude/codehero/scripts/claude-daemon.py` | AI ticket system prompt |
| smart_context.py | `/home/claude/codehero/scripts/smart_context.py` | Context injection |
| mcp_server.py | `/home/claude/codehero/scripts/mcp_server.py` | MCP tools |
| **setup.sh** | `/home/claude/codehero/setup.sh` | Fresh install - δημιουργία references/ |
| **upgrade.sh** | `/home/claude/codehero/upgrade.sh` | Upgrade - δημιουργία αν δεν υπάρχει |
| **_always.sh** | `/home/claude/codehero/upgrades/_always.sh` | Τρέχει πάντα σε upgrade |

---

## ΕΠΟΜΕΝΑ ΒΗΜΑΤΑ

1. [x] Δημιουργία `codehero_import_project` MCP tool ✅ (2026-01-20)
2. [x] Δημιουργία `codehero_analyze_project` MCP tool ✅ (2026-01-20)
3. [x] Δημιουργία `/opt/codehero/references/` folder structure ✅ (2026-01-20)
4. [x] **Ενημέρωση `setup.sh`** - προσθήκη references folder ✅ (2026-01-20)
5. [x] **Ενημέρωση `_always.sh`** - δημιουργία references αν δεν υπάρχει ✅ (2026-01-20)
6. [x] Ενημέρωση CLAUDE.md με οδηγίες import ✅ (2026-01-20)
7. [x] Ενημέρωση project-template.md με section για existing code ✅ (2026-01-20)
8. [x] Ενημέρωση daemon system prompt για reference projects ✅ (2026-01-20)
9. [ ] Testing με πραγματικό project import
