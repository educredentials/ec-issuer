---
name: docs-writer
description: Write documentation following consistent, clear, and user-focused style. Use when creating or editing documentation files.
---

# Documentation Writing Skill


## When writing documentation

### Start here

1. **Who is this for?** Match complexity to audience. Don't oversimplify hard things or overcomplicate simple ones.
2. **What do they need?** Get them to the answer fast. Nobody wants to be in docs longer than necessary.
3. **What did you struggle with?** Those common questions you had when learning? Answer them (without literally including the question).

### Technical stack

Located at `./docs/src`.
Uses mdbook, configured via `./docs/src/book.toml` and built in the CI using `.github/workflows/docuementation.yaml`
Command `just docs` will start a server (in the foreground) that builds and serves the docs

The file SUMMMARY.md contains the outline of the entire documentation. New pages must be placed in here.

Some documentation files are symlinks to files used elsewhere in this project, like the README.md

### Writing process

**Draft:**

- Write out the steps/explanation as you'd tell a colleague
- Lead with what to do, then explain why
- Use headings that state your point: "Set SAML before adding users" not "SAML configuration timing"

**Edit:**

- Read aloud. Does it sound like you talking? If it's too formal, simplify.
- Cut anything that doesn't directly help the reader
- Check each paragraph has one clear purpose
- Verify examples actually work (don't give examples that error)

**Integrate**

- Look at related pages and check if they do not conflict the new documentation.
- Look at related pages and check if there is overlap. If so, edit either one to remove duplication.
- Link to these related pages from the current page, where appropriate.
- Link to this new or edited page from the related pages, where appropriate.

**Polish:**

- Make links descriptive (never "here")
- Backticks only for code/variables, **bold** for UI elements
- American spelling, serial commas
- Keep images minimal and scoped tigh


### Common patterns

**Instructions:**

```markdown
Run:
\`\`\`
command-to-run
\`\`\`

Then:
\`\`\`
next-command
\`\`\`

This ensures you're getting the latest changes.
```

Not: "(remember to run X before Y...)" buried in a paragraph.

**Headings:**

- "Use environment variables for configuration" ✅
- "Environment variables" ❌ (too vague)
- "How to use environment variables for configuration" ❌ (too wordy)
- "3. Configuration" X (Adds numbers)

Do not add numbers to headers, the documentation tooling will do that for us, and will lead to double numberings that might even conflic.

Start with header level 1 `# The main header` at the top
Use level 2 for subdividing, 3 for even more, etc. Never go over level 3.
Ensure level hierarcy is correct. So no header 3 without a header 2 above it.

**Links:**

- "Check out the [SAML documentation](link)" ✅
- "Read the docs [here](link)" ❌

Prefer links to explanation. So don't explain the steps to install "some third party tool" but instead just link to their installation, or even main documentation.

### Watch out for

- Describing tasks as "easy" (you don't know the reader's context)
- Using "we" when talking about Metabase features (use "Metabase" or "it")
- Formal language: "utilize", "reference", "offerings"
- Too peppy: multiple exclamation points
- Burying the action in explanation
- Code examples that don't work
- Numbers that will become outdated

### Quick reference

| Write This                 | Not This           |
| -------------------------- | ------------------ |
| people, companies          | users              |
| summarize                  | aggregate          |
| take a look at             | reference          |
| can't, don't               | cannot, do not     |
| **Filter** button          | \`Filter\` button  |
| Check out [the docs](link) | Click [here](link) |
