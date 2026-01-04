import os
from datetime import datetime

from .builderbase import BuilderBase
from .build_ver_mgr import BuildVerMgr
from ..template.main_registry import MainRegistry
from ..template.process.process_obsidian_templates import ProcessObsidianTemplates
from ..template.prompt.single.support_processor import SupportProcessor
from ..config.pkg_config import PkgConfig
from ..template.process.read_obsidian_template_meta import ReadObsidianTemplateMeta
from ..template.process_single.engines.registry.template_registry_processor import (
    TemplateRegistryProcessor,
)
from ..template.process_single.engines.templates.template_processor import (
    TemplateProcessor,
)
from ..template.process_single.engines.enforcement.enforcement_processor import (
    EnforcementProcessor,
)
from ..template.process_single.manifest_creator import ManifestCreator


class SingleBuilder(BuilderBase):
    def __init__(self, build_version: int = 0):
        super().__init__()
        self.config = PkgConfig()
        self._build_version = build_version
        self._batch_hash = ""
        self._batch_date = None
        self._current_user = self.config.env_user

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

        # self._destination_path = (
        #     self.config.root_path
        #     / self.config.pkg_out_dir
        #     / f"single-{self._build_version}"
        # )
        self._destination_path = self.config.config_cache.get_dist_single(
            self._build_version
        )
        self._destination_path.mkdir(parents=True, exist_ok=True)

        self._main_registry = MainRegistry(build_version=self._build_version)

    def build_package(self):
        current_date = self.batch_date.isoformat()
        meta_reader = ReadObsidianTemplateMeta()
        template_meta = meta_reader.read_template_meta()

        process_templates = ProcessObsidianTemplates()

        processed_template_data = process_templates.process(
            {
                "declared_registry_id": self._main_registry.reg_id,
                "declared_registry_version": self._main_registry.reg_version,
                "mapped_registry": self._main_registry.reg_id,
                "mapped_registry_minimum_version": self._main_registry.reg_version,
                "batch_number": str(self._build_version),
            }
        )
        templates_data = {}
        for _, fm in processed_template_data.items():
            templates_data[fm.template_type] = fm

        tp = TemplateProcessor(
            workspace_dir=self._destination_path,
            registry=self._main_registry,
            templates_data=templates_data,
        )
        fm_data = tp.execute_all(tokens={})

        trp = TemplateRegistryProcessor(
            workspace_dir=self._destination_path,
            registry=self._main_registry,
            templates_meta=template_meta,
            templates_data=fm_data,
        )
        _ = trp.execute_all(tokens={})

        support_processor = SupportProcessor(registry=self._main_registry)
        support_processor.execute_all(
            tokens={
                "VER": str(self._build_version),
                "TEMPLATES_DATA": processed_template_data,
            }
        )
        ep = EnforcementProcessor(
            workspace_dir=self._destination_path,
            registry=self._main_registry,
            templates_data=templates_data,
        )
        _ = ep.execute_all(
            tokens={
                "DATE": current_date,
                "VER": str(self._build_version),
            }
        )
        mc = ManifestCreator(build_number=self._build_version)
        mc.create_manifest(templates=fm_data)
        # template_count = tp.Count

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
