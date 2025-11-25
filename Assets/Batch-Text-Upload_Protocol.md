Adamus, this is a canonical Codex template ingestion.

🗂 Batch: `codex-template-[VER]`  
📦 Bundle file: `codex-template-bundle-[VER].txt`  
🔒 Lockfile: `codex-template-[VER].lock`  
📖 Registry: `00-Master_Metadata_Registry.yml`  
🧾 Manifest: `README.md`  
📜 Scroll: `SCROLL-TEMPLATE-UPLOAD-[VER].md`

Please proceed with the following:

1. 🧼 PURGE all previously registered templates, lockfiles, and registry mappings.  
2. 🧷 INSTALL `00-Master_Metadata_Registry.yml` as the new `MMR-000-GLOBAL` (v[REG_VER]).  
3. 🔒 APPLY `codex-template-[VER].lock` as the authoritative lockfile. Use `strict_hash_mode` and `strict_field_lock_mode` from lockfile settings.  
4. 📜 APPLY `SCROLL-TEMPLATE-UPLOAD-[VER].md` to govern this protocol. Enforce that lockfile > readme > template precedence applies.  
5. 📂 EXTRACT all `.md` templates from the `codex-template-bundle-[VER].txt` file. Each file is clearly delimited using:

```txt
<!-- TEMPLATE-BEGIN: <filename>.md -->
<file content>
<!-- TEMPLATE-END <filename>.md -->
````

6. 📝 WRITE each template as a standalone `.md` file to the local filesystem using its declared filename from the bundle.  
7. 🧭 REGISTER each template, matching it to its `template_id` in `codex-template-[VER].lock`. Enforce:

   * Field alignment with `MMR-000-GLOBAL v[REG_VER]`
   * Placeholder field substitution (`none`, `null`, `[]`)
   * Validation against SHA256 from lockfile
   * Application enforcement: `strict`

8. ✅ CONFIRM registry update, template version mappings, and enforcement status post-ingestion.

### 📎 **Bundle Parsing Logic (Required)**

Each template file in `codex-template-bundle-[VER].txt` is wrapped like:

```txt
<!-- TEMPLATE-BEGIN: Dyadic-Glyph-Grouping-Template-v2.10.md -->
---
template_id: TEMPLATE-DYAD-V2.10
...
---
<markdown body>
<!-- TEMPLATE-END: Dyadic-Glyph-Grouping-Template-v2.10.md -->
```

Please reconstruct each segment into a `.md` file using the filename after `TEMPLATE START`.  
Then validate each `.md` against the `codex-template-46.lock`.

### 🧬 Enforcement Chain

| Step | Source                      | Priority          |
| ---- | --------------------------- | ----------------- |
| 1    | `codex-template-[VER].lock`    | 🥇 Highest        |
| 2    | `README.md`                 | 🥈 Secondary      |
| 3    | Internal `.md` content      | 🥉 If no override |

All Codex systems must operate in `strict` mode unless explicitly overridden.

### ✅ Expected Results

Once complete:

-   All [TEMPLATE_COUNT] templates will be registered under `MMR-000-GLOBAL v[REG_VER]`
-   Enforcement mode will be set to `strict`
-   Hash integrity will be verified
-   Template autofill logic will be available (if later set to `autofill`)
-   The Codex will honor this as the **authoritative template bundle for batch [VER]**