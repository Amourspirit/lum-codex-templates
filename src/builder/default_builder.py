import os
import zipfile
from datetime import datetime

from .builderbase import BuilderBase
from .build_ver_mgr import BuildVerMgr
from ..template.main_registery import MainRegistry
from ..template.front_mater_meta import FrontMatterMeta
from ..template.process.process_obsidian_templates import ProcessObsidianTemplates
from ..template.process.pkg_companions.processor import PkgCompanionsProcessor
from ..template.process.prompt.prompt_bootstrap import PromptBootstrap
from ..config.pkg_config import PkgConfig


class DefaultBuilder(BuilderBase):
    def __init__(self, build_version: int = 0):
        super().__init__()
        self.config = PkgConfig()
        self._build_version = build_version
        self._main_registry = MainRegistry()
        self._destination_path = self.config.root_path / self.config.pkg_out_dir
        self._destination_path.mkdir(parents=True, exist_ok=True)
        self._batch_hash = ""
        self._batch_date = None
        if os.getenv("CURRENT_USER") is None:
            self._current_user = self.config.current_user
        else:
            self._current_user = os.getenv("CURRENT_USER")

        # if VERSION_OVERRIDE in in the environment, use it
        env_version = os.getenv("VERSION_OVERRIDE")
        if env_version and env_version.isdigit():
            self._build_version = int(env_version)
        elif self.config.version_override > 0:
            self._build_version = self.config.version_override
        else:
            if self._build_version <= 0:
                bvm = BuildVerMgr()
                self._build_version = bvm.get_next_version()
                bvm.version = self._build_version
                bvm.save_current_version()

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

        template_count = 0
        # === Create ZIP ===
        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Dictionary to group templates by category dynamically
            processs_templates = ProcessObsidianTemplates()

            with processs_templates.process(
                {
                    "declared_registry_id": self._main_registry.reg_id,
                    "declared_registry_version": self._main_registry.reg_version,
                    "mapped_registry": self._main_registry.reg_id,
                    "mapped_registry_minimum_version": self._main_registry.reg_version,
                }
            ) as processed_template_paths:
                template_paths = {}
                for key, file_path in processed_template_paths.items():
                    fm = FrontMatterMeta(file_path)
                    if not fm.has_field("template_id"):
                        continue
                    template_count += 1
                    zipf.write(file_path, arcname=file_path.name)
                    template_paths[key] = file_path

                pcp = PkgCompanionsProcessor(self._main_registry)
                companion_results = pcp.execute_all(
                    {
                        "VER": str(self._build_version),
                        "BATCH_HASH": self.batch_hash,
                        "BUILDER_VER": self.config.version,
                        "DATE": self.batch_date.isoformat(),
                        "TEMPLATE_COUNT": template_count,
                        "TEMPLATE_PATHS": template_paths,
                    }
                )
                for _, result_path in companion_results.items():
                    zipf.write(result_path, arcname=result_path.name)

                pcp.cleanup()

        pb = PromptBootstrap(self._main_registry)
        pb.process(
            {
                "CURRENT_USER": self._current_user,
                "TEMPLATE_COUNT": template_count,
                "VER": str(self._build_version),
            }
        )
        print(f"Built package: {output_zip_path}")

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
