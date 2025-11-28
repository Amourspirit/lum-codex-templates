import zipfile
from datetime import datetime

from .builderbase import BuilderBase
from ..template.main_registery import MainRegistry
from ..template.front_mater_meta import FrontMatterMeta
from ..template.process.process_obsidian_templates import ProcessObsidianTemplates
from ..template.process.pkg_companions.processor import PkgCompanionsProcessor


class DefaultBuilder(BuilderBase):
    def __init__(self, build_version: str):
        super().__init__()
        self._build_version = build_version
        self._main_registry = MainRegistry()
        self._destination_path = self.config.root_path / self.config.pkg_out_dir
        self._destination_path.mkdir(parents=True, exist_ok=True)
        self._batch_hash = ""
        self._batch_date = None

    def build_package(self):
        # === Paths ===
        output_zip_name = f"{self.config.package_output_name}-{self._build_version}.zip"
        output_zip_path = self._destination_path / output_zip_name
        if output_zip_path.exists():
            output_zip_path.unlink()

        lock_file_name = f"{self.config.lock_file_name}-{self._build_version}{self.config.lock_file_ext}"
        lockfile_path = self._destination_path / lock_file_name
        if lockfile_path.exists():
            lockfile_path.unlink()

        # === Create ZIP ===
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Dictionary to group templates by category dynamically
            processs_templates = ProcessObsidianTemplates()

            template_count = 0

            with processs_templates.process(
                {
                    "declared_registry_id": self._main_registry.reg_id,
                    "declared_registry_version": self._main_registry.reg_version,
                    "mapped_registry": self._main_registry.reg_id,
                    "mapped_registry_minimum_version": self._main_registry.reg_version,
                }
            ) as processed_template_paths:
                for file_path in processed_template_paths:
                    fm = FrontMatterMeta(file_path)
                    if not fm.has_field("template_id"):
                        continue
                    template_count += 1
                    zipf.write(file_path, arcname=file_path.name)

                pcp = PkgCompanionsProcessor(self._main_registry)
                companion_results = pcp.execute_all(
                    {
                        "VER": self._build_version,
                        "BATCH_HASH": self.batch_hash,
                        "BUILDER_VER": self.config.version,
                        "DATE": self.batch_date.isoformat(),
                        "TEMPLATE_COUNT": template_count,
                        "SHA256": self.compute_sha256(output_zip_path),
                        "TEMPLATE_PATHS": [p for p in processed_template_paths],
                    }
                )
                for _, result_path in companion_results.items():
                    zipf.write(result_path, arcname=result_path.name)

                pcp.cleanup()

    @property
    def batch_date(self) -> datetime:
        if not self._batch_date:
            self._batch_date = datetime.now().astimezone()
        return self._batch_date

    @property
    def batch_hash(self) -> str:
        if not self._batch_hash:
            self._batch_hash = self.compute_time_hash()
        return self._batch_hash
