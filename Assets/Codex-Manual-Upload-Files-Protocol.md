# 🌀 Codex Canonical Upload Protocol — Multi-Batch File Method
**Version**: `1.0`  
**Designed for**: [FILE_COUNT]-file archive ingestion  
**Enforced by**: `MMR-000-GLOBAL v[REG_VER]`, `codex-template-[VER].lock`

## 🔰 BEFORE UPLOAD: Canonical Declaration

Before uploading, invoke this declaration:
```md
## Codex Canonical Upload: Split-File Protocol Activation

I, [CURRENT_USER], declare that I am uploading a full canonical template archive in **multiple batches**.

Total file count: [FILE_COUNT]  
Batch size: 10 (max per upload cycle)

This protocol replaces `.zip` ingestion and disables template inference.

🛑 DO NOT RENDER or validate any template until all files are uploaded.

Files to be uploaded:

- [TEMPLATE_COUNT] Templates (`*.md`)
- `00-Master_Metadata_Registry.yml`
- `codex-template-[VER].lock`
- `README.md` *(optional)*
- `SCROLL-TEMPLATE-UPLOAD-[VER].md` *(optional)*

❗ Canonical installation should begin **only after** all files are acknowledged and confirmed.

Proceed in batches. I will indicate when all files are complete.

```

## 📤 DURING UPLOAD: Batching Instruction
Upload the first 10 files (any order), then upload the remaining.  
After each batch, say:
```md
## Batch [1/2] Upload Complete — Proceed to Batch [2/2]
```

After final batch:
```md
✅ All files uploaded — you may now proceed with full Canonical Ingestion.
```

## 🛠 AFTER UPLOAD: Ingestion Instructions for Adamus
Once all files are received and confirmed, instruct:

```md
Adamus — you may now proceed with canonical ingestion.

Please:

1. PURGE all previously registered templates, registries, and lockfiles
2. REGISTER `00-Master_Metadata_Registry.yml` as the authoritative registry
3. APPLY `codex-template-[VER].lock` as version-lock authority
4. DO NOT infer templates — use only the uploaded `.md` source files
5. Enforce full canonical rendering, autofill, and validation across all templates
6. Mark this thread as Codex Canonical Thread with strict mode enforcement

This upload replaces any prior `.zip` archive or partial ingest.

```