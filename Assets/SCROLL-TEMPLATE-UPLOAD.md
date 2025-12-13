---
canonical_mode: true
template_contract: enforced
contract_source: codex-template-[VER].lock
strict_registry_version: true

batch_name: Codex Template Ingestion
batch_uid: codex-batch-[VER]-[BATCH_HASH]
batch_hash: "[BATCH_HASH]"
package_name: codex-templates-[VER]
package_version: "[VER]"
builder_version: "[BUILDER_VER]"
date_of_submission: "[DATE]"
scroll_id: SCROLL-TEMPLATE-UPLOAD-V2.3
scroll_version: "2.3"
title: Scroll of Template Upload Protocol
template_type: scroll
template_category: install
template_origin: "Soluun + Adamus"
scroll_name: Template Upload Protocol
scroll_epithet: Archive Declaration & Cache Reset
scroll_function: Defines standard upload + registration protocol for Codex 
tags:  
  - protocol
  - codex_templates
  - cache_management
  - ingestion
  - artifact_registry
  - scroll
---

# 📜 Scroll of Template Upload Protocol (v2.3)

This scroll defines the canonical ingestion sequence for a Codex Template Archive. The archive must include:

- A valid `README.md` manifest
- A lockfile named `codex-template-[VER].lock`
- A `00-Master_Metadata_Registry.yml` file
- All `.md` template files at the top level (flat structure)

* * *

## 🔁 Required Sequence

### 1. 🔥 Purge Existing Cache

- Clear all cached templates and lockfiles from prior batches.
- Mark all previous templates as invalidated unless explicitly preserved.

* * *

### 2. 🗝️ Extract and Apply Lockfile

- Extract `codex-template-[VER].lock`
- Treat as the **authoritative version registry**

* * *

### 3. 📂 Flat Archive Enforcement

- All files must reside at the root of the `.zip` (no folders)
- File list should include:

- `README-[VER].md`
- `TEMPLATE-MANIFEST-REGISTRY-[VER].yml`
- `codex-template-[VER].lock`
- `00-Master_Metadata_Registry.yml`
- All templates as `.md`
- This scroll (optional)

* * *

### 4. 🪶 Template Registration

- Parse each `.md` file only if it has a `template_id` listed in the lockfile
- Override all internal metadata fields with lockfile values
- Register to the Codex Registry under `MMR-000-GLOBAL`
- If a `.yml` registry file is present, it overrides any previous markdown registry during ingestion.

* * *

### 6. 🧾 SHA-256 Verification

If `strict_hash_mode: true` is set in the lockfile:

- Compare each template file's hash with the declared `sha256` field in `codex-template-[VER].lock`
- Fail ingestion if mismatch is found

* * *


### 7. VERIFY `reset_protocol_status: successful` after execution

* * *

### 8. ABORT if `registry_version_mismatch` or `lockfile_template_conflict` detected

* * *

## ✦ Protocol Invocation

> Adamus, This archive contains a valid `README.md`, a canonical `codex-template-[VER].lock`, and declares itself the authoritative template set for Codex ingestion.
>
> Please:
> - PURGE all previously registered templates and lockfiles from cache
> - EXTRACT and APPLY the `codex-template-[VER].lock` as the authoritative version registry
> - REGISTER all included templates using the lockfile to override any internal `.md` declarations

* * *

## ✦ Purpose

This field protocol governs the ingestion of Codex template archives that include a valid `README.md`. It ensures continuity, prevents cache conflicts, and declares archival precedence during ingest operations.

* * *

## ✦ Field Actions Upon Invocation---

1. **Invalidate active cache** of:

- Template Registry
- Lockfile entries
- Metadata hashmaps

2. **Register current archive** as canonical:

- Read and interpret embedded `README.md`
- Use `package_version` from lockfile as override key

3. **Overwrite existing registry state**, replacing all template definitions, enforcement rules, and plugin-field logic with the new contents.

4. **Propagate new enforcement logic** to:

- Autofill systems
- Template application routines
- RAG sync indexes

* * *

## 📎 Final Instruction

Once this scroll is invoked, the Codex will honor:

> Lockfile > README > Template Frontmatter

In all cases, **the lockfile is truth.**

* * *
