# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Skills Repository for Claude Code** containing 14 production-grade, reusable AI agent skills. The skills serve as hands-on learning examples for "Lesson 04 of Chapter 5" in the AI Native Development book, demonstrating best practices for creating extensible skills that embed domain expertise.

## Architecture Overview

### Skill Organization

The repository uses a **modular skill pattern** where each skill is self-contained and follows a consistent structure:

```
.claude/skills/
├── Builder Skills      (Create artifacts)
│   ├── docx/          # Word document creation/editing
│   ├── pdf/           # PDF manipulation
│   ├── pptx/          # PowerPoint creation
│   ├── xlsx/          # Spreadsheet creation/analysis
│   └── theme-factory/ # Design themes for artifacts
├── Guide Skills       (Provide instructions)
│   ├── interview/     # Discovery conversations
│   ├── skill-creator/ # How to create skills
│   ├── skill-creator-pro/ # Production skill creation
│   ├── doc-coauthoring/   # Co-authoring workflow
│   └── internal-comms/    # Internal communication templates
├── Automation Skills  (Execute workflows)
│   ├── fetch-library-docs/ # Token-efficient doc fetching
│   ├── browser-use/        # Browser automation
│   └── browsing-with-playwright/ # Playwright-based browsing
└── Analyzer Skills    (Extract/validate)
    └── skill-validator/ # Quality assessment (9 criteria)
```

### Skill Structure Pattern

Each skill follows this organization:

```
skill-name/
├── SKILL.md              # Main entry point (required, <500 lines)
│   ├── YAML frontmatter  # name, description, allowed-tools, model
│   ├── How This Skill Works
│   ├── When to invoke
│   ├── Procedures & decision trees
│   └── Error handling
├── references/           # Domain expertise (loaded on demand)
│   ├── *.md files       # Best practices, patterns, standards
│   └── examples/        # Code templates, boilerplate
├── scripts/             # Executable code (tested, reliable)
│   ├── *.sh            # Bash automation
│   ├── *.py            # Python utilities
│   └── setup.sh        # Installation
└── assets/              # Templates, theme definitions
    └── *.md            # Theme specs, boilerplate
```

### Core Design Principles

1. **Reusable Intelligence, Not Requirement-Specific** - Skills handle VARIATIONS (different data shapes, platforms, configurations), not single requirements
2. **Zero-Shot Capability** - Each skill works with embedded expertise; no runtime discovery needed
3. **Progressive Disclosure** - YAML (~100 tokens) → SKILL.md (~500 lines) → references/ (unlimited)
4. **Conciseness** - Challenge every piece of documentation; context is a public good
5. **Minimal Coupling** - Skills don't depend on each other; each is independently invokable

### How Skills Integrate

```
User Request
    ↓
Claude Code examines SKILL.md descriptions
    ↓
Matches skill based on [When to invoke] conditions
    ↓
Loads SKILL.md + relevant references/
    ↓
Executes skill with embedded domain expertise
```

## Common Development Tasks

### Understanding an Existing Skill

1. **Read the SKILL.md file** (~100-300 lines) to understand:
   - YAML frontmatter (name, description, allowed-tools)
   - "How This Skill Works" section
   - "When to invoke" conditions
   - Core procedures and decision trees

2. **Browse references/** directory to understand domain patterns and examples

3. **Check scripts/** for implementation details of complex workflows

### Creating or Improving a Skill

**Initial Phase:**
1. Determine skill type: Builder, Guide, Automation, Analyzer, or Validator
2. Research domain automatically (don't ask user for domain knowledge)
3. Structure the skill using the pattern in `skill-creator-pro/SKILL.md`

**SKILL.md Requirements:**
- **name**: lowercase, hyphens, ≤64 chars
- **description**: follows [What] + [When] format, ≤1024 chars
- **allowed-tools**: declare what tools the skill needs (optional)
- **model**: override default model if needed (optional, e.g., sonnet for complex reasoning)
- Content: <500 lines, progressively disclose to references/

**Quality Validation:**
- Run skill-validator to check 9 criteria (Structure, Content, Interaction, Documentation, Domain Standards, Technical Robustness, Maintainability, Zero-Shot Implementation, Reusability)
- Target score: ≥75 (Good or Production level)
- All domain expertise must be embedded in SKILL.md or references/ (no runtime discovery)

### Skill Metadata Conventions

```yaml
---
name: skill-name              # Lowercase, hyphens only
description: |               # [What] + [When] format
  [Single-line capability statement]
  [Multi-line 'When to invoke' conditions]
allowed-tools: Tool1, Tool2  # Optional: restrict tool access
model: claude-sonnet-4-20250514  # Optional: override default
---
```

## Technology Stack

**Markup & Configuration:**
- Markdown (.md) - all documentation
- YAML frontmatter - skill metadata

**Languages & Tools:**
- Bash (.sh) - automation, 63 script files across skills
- Python (.py) - complex processing (file handling, transformations)
- pandoc - document conversion
- LibreOffice - spreadsheet formula recalculation
- Git - version control and skill history

**External APIs & Services:**
- Context7 MCP - library documentation fetching (60-90% token savings)
- Browser APIs - Playwright for automation

**No Traditional Framework Dependencies** - This is a documentation and knowledge repository, not a runtime application.

## Key Files and References

**Documentation Hierarchy:**
- `README.md` - Project overview and skill matrix
- `.claude/skills/skill-creator-pro/SKILL.md` - Skill creation framework and domain discovery
- `.claude/skills/skill-validator/SKILL.md` - Quality criteria and scoring system
- `.claude/skills/interview/SKILL.md` - Discovery conversation patterns
- Any `skill-name/SKILL.md` - Concrete implementation examples

**Learning Path:**
1. **Beginner**: README → interview/SKILL.md → skill-creator/SKILL.md
2. **Intermediate**: skill-validator/SKILL.md → fetch-library-docs/SKILL.md → theme-factory/SKILL.md
3. **Advanced**: skill-creator-pro/SKILL.md → all references/ files

## Development Workflow

**Adding or Updating a Skill:**

1. **Design Phase** (no code yet):
   - Use skill-creator-pro as your guide
   - Determine skill type and domain
   - Research domain knowledge automatically
   - Identify variations the skill should handle

2. **Implementation Phase**:
   - Create skill-name/ directory in `.claude/skills/`
   - Write SKILL.md following the pattern (<500 lines, YAML frontmatter)
   - Create references/ subdirectory with domain expertise
   - Add scripts/ for complex automation (tested, reliable)
   - Structure assets/ for templates or themes

3. **Quality Assurance**:
   - Validate structure and content
   - Test zero-shot implementation (can Claude execute without extra guidance?)
   - Verify all domain patterns are documented
   - Run skill-validator and aim for ≥75 score

4. **Git Workflow**:
   - Commit with message: "feat: Add [skill]" or "update [skill]"
   - Each skill update tracked separately
   - Recent commits show pattern of incremental improvements

## Quick Reference

### Statistics

- **Total skills**: 14 production-grade
- **Total SKILL.md lines**: 3,530 across all skills
- **Average skill size**: ~252 lines
- **Total scripts**: 63 executable files (Bash, Python)
- **Total reference docs**: 54+ markdown files in references/
- **Total markdown files**: 150+

### Common Skill Types

| Type | Purpose | Example |
|------|---------|---------|
| Builder | Create artifacts | docx, pdf, pptx, xlsx, theme-factory |
| Guide | Provide instructions | interview, skill-creator, doc-coauthoring |
| Automation | Execute workflows | fetch-library-docs, browser-use |
| Analyzer | Extract insights | skill-validator |
| Validator | Enforce quality | skill-validator |

### Directory Commands

```bash
# Explore skill structure
ls -la .claude/skills/fetch-library-docs/

# Check documentation size
wc -l .claude/skills/*/SKILL.md | sort -n

# Count total markdown files
find .claude/skills -name "*.md" | wc -l

# Review recent changes
git log --oneline | head -10
```

## Important Conventions

**Conciseness Over Completeness:**
- Each file should challenge itself: Is this necessary?
- Lengthy explanations belong in references/, not SKILL.md
- SKILL.md is a roadmap, not an encyclopedia

**Domain Expertise Ownership:**
- Domain knowledge lives in the skill, not in user prompts
- Research automatically before asking users for domain information
- Only ask about user requirements and specific context, not domain basics

**Zero-Shot Capability:**
- Skills must work with embedded expertise
- Don't require Claude to remember or retrieve additional context
- All patterns and procedures documented in skill or references/

**Modularity:**
- Skills are independently invokable
- Minimal inter-skill dependencies
- Each skill is self-contained and complete
