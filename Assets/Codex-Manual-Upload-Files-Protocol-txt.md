# 🌀 Codex Canonical Upload Protocol — Multi-Batch File Method (TXT Variant)
**Version**: `1.1`  
**Designed for**: [FILE_COUNT]-file archive ingestion  
**Enforced by**: `MMR-000-GLOBAL v[REG_VER]`, `codex-template-[VER].lock`

## 🔰 BEFORE UPLOAD: Canonical Declaration

Before uploading, invoke this declaration:
```md
## Codex Canonical Upload: Split-File Protocol Activation (TXT Variant)

I, [CURRENT_USER], declare that I am uploading a full canonical template archive in **multiple batches** using `.txt` format.

Total file count: [FILE_COUNT]  
Batch size: 10 (max per upload cycle)

This protocol replaces `.zip` ingestion and disables template inference.

🛑 DO NOT RENDER, VALIDATE, OR INFER any template until all files are uploaded and acknowledged.

Files to be uploaded:

- 11 Templates (`*.txt` instead of `*.md`)
- `00-Master_Metadata_Registry.yml`
- `codex-template-[VER].lock`
- `README.md` *(optional, use `.txt` if needed)*
- `SCROLL-TEMPLATE-UPLOAD-[VER].md` *(optional, use `.txt` if needed)*

Canonical installation should begin **only after** all files are received.


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
Adamus — begin Canonical Ingestion using uploaded `.txt` templates.

Please:

1. PURGE all previous templates, registries, and lockfiles
2. REGISTER `00-Master_Metadata_Registry.yml` as the authoritative registry
3. APPLY `codex-template-[VER].lock` as the version-lock authority
4. REGISTER all `.txt` templates as canonical, treating them as `.md` internally
5. Enforce all field and threshold rules as defined in `MMR-000-GLOBAL v2.5`
6. DO NOT infer templates — all structure must derive from uploaded `.txt` sources

This completes Canonical Thread Bootstrap for `codex-templates-[VER]`.

```