import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from jinja2 import Template
from loguru import logger
from fastapi import APIRouter, HTTPException, status

# from fastapi_cache.decorator import cache
import mcp
from pydantic import ValidationError

# from ..routes.limiter import limiter
from ...models.templates.artifact_submission import ArtifactSubmission
from ...models.templates.upgrade_to_template_submission import (
    UpgradeToTemplateSubmission,
)
from ...models.templates.template_status_response import TemplateStatusResponse
from ...models.templates.verify_artifact_response import (
    VerifyArtifactApiResponse,
    VerifyArtifactMcpResponse,
    VerifyArtifactResponse,
)
from ...models.templates.finalize_artifact_response import FinalizeArtifactResponse
from ...models.templates.upgrade_artifact_response import (
    UpgradeArtifactMcpResponse,
    UpgradeArtifactResponse,
    UpgradeArtifactApiResponse,
)
from ...models.templates.manifest_response import ManifestResponse
from ...models.templates.template_response import TemplateResponse
from ...models.templates.template_instruction_response import (
    TemplateInstructionsResponse,
)
from ..cleanup.clean_meta_fields import CleanMetaFields
from ..upgrade.upgrade_template import UpgradeTemplate
from ..util.result import Result
from ..verify.verify_meta_fields import VerifyMetaFields
from ..content_processors.pre_processors.pre_process_template import (
    PreProcessTemplate,
)
from ..content_processors.pre_processors.pre_process_registry import (
    PreProcessRegistry,
)
from src.template.front_mater_meta import FrontMatterMeta
from src.config.pkg_config import PkgConfig
from api.config import Config
from api.lib.kind import ServerModeKind
from api.lib.exceptions import (
    VersionError,
    VersionLatestError,
    VersionEmptyError,
    VersionFormatError,
    VersionNoneError,
)
from . import fn_versions

_CONFIG = Config()
_SETTINGS = PkgConfig()

router = APIRouter(prefix=f"{_CONFIG.api_v1_prefix}/templates", tags=["Templates"])
_API_RELATIVE_URL = _CONFIG.api_v1_prefix
_TEMPLATE_DIR = _SETTINGS.config_cache.get_api_templates_path()


def _validate_version_str(
    version: str | None,
) -> Result[str, None] | Result[None, VersionError]:
    if version is None:
        return Result(None, VersionNoneError("Version cannot be None."))
    if not version:
        return Result(None, VersionEmptyError("Version cannot be empty."))
    v = version.strip().lower()
    if v == "latest":
        return Result(None, VersionLatestError("Version 'latest' is not allowed here."))
    v = v.lstrip("v")
    if not v:
        return Result(None, VersionEmptyError("Version cannot be empty."))
    if not v.replace(".", "").isdigit():
        return Result(None, VersionFormatError("Invalid version format."))
    if v.isdigit():
        v = f"{v}.0"
    if not v.startswith("v"):
        v = "v" + v
    return Result(v, None)


def _get_template_manifest(
    template_type: str,
    version: str,
    app_root_url: str,
    server_mode_kind: ServerModeKind,
) -> dict[str, Any]:
    logger.debug(
        "Fetching manifest for template_type: {template_type}, version: {version}",
        template_type=template_type,
        version=version,
    )
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data

    path = _TEMPLATE_DIR / template_type / ver / "manifest.json"

    if not path.exists():
        raise HTTPException(status_code=404, detail="Manifest file not found.")
    json_content: dict = json.loads(path.read_text())
    if server_mode_kind == ServerModeKind.API and app_root_url:
        json_content["template_api_path"] = (
            f"{app_root_url}/{_TEMPLATE_DIR.name}/{template_type}/{ver}"
        )
        json_content["instructions_api_path"] = (
            f"{app_root_url}/{_TEMPLATE_DIR.name}/{template_type}/{ver}/instructions"
        )
        json_content["registry_api_path"] = (
            f"{app_root_url}/{_TEMPLATE_DIR.name}/{template_type}/{ver}/registry"
        )
        json_content["manifest_api_path"] = (
            f"{app_root_url}/{_TEMPLATE_DIR.name}/{template_type}/{ver}/manifest"
        )
        json_content["executor_mode_api_path"] = (
            f"{app_root_url}/executor_modes/{json_content['canonical_mode']['executor_mode']}-V{json_content['canonical_mode']['version']}"
        )
    return json_content


def _get_template_registry(template_type: str, version: str) -> dict[str, Any]:
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        logger.error(
            "Version validation failed: {v_result_error}", v_result_error=v_result.error
        )
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data
    path = _TEMPLATE_DIR / template_type / ver / "registry.json"
    if not path.exists():
        logger.error("Registry file not found at path: {path}", path=path)
        raise HTTPException(status_code=404, detail="Registry file not found.")
    json_content = cast(dict[str, Any], json.loads(path.read_text()))
    return json_content


async def get_template(
    template_type: str,
    version: str,
    app_root_url: str,
    monad_name: str | None = None,
    server_mode_kind: ServerModeKind = ServerModeKind.API,
) -> TemplateResponse:
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        logger.error(
            "Version validation failed: {v_result_error}", v_result_error=v_result.error
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_result.error)
        )
    ver = v_result.data
    path = _TEMPLATE_DIR / template_type / ver / "template.md"
    if not path.exists():
        logger.error("Template file not found at path: {path}", path=path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template file not found."
        )
    fm = FrontMatterMeta(file_path=path)
    if fm.has_field("template_registry"):
        api_path = f"{app_root_url}/{_TEMPLATE_DIR}/{template_type}/{ver}/registry"
        fm.frontmatter["template_registry"]["api_path"] = api_path
        fm.recompute_sha256()

    if not fm.has_field("instruction_info"):
        fm.set_field("instruction_info", {})
    fm.frontmatter["instruction_info"]["id"] = "instructions"
    fm.frontmatter["instruction_info"]["api_path"] = (
        f"{app_root_url}/{_TEMPLATE_DIR}/{template_type}/{ver}/instructions"
    )
    text = fm.get_template_text()
    try:
        if monad_name:
            pre_processor = PreProcessTemplate(
                template_content=text, monad_name=monad_name
            )
            processed_text = pre_processor.pre_process_template()
            logger.debug(
                "Processed template with monad: {monad_name}", monad_name=monad_name
            )
            return TemplateResponse(
                content=processed_text,
                template_type=template_type,
                template_version=ver,
            )
        else:
            logger.debug("No monad name provided, skipping pre-processing.")
    except Exception as error:
        logger.error("Error during template pre-processing: {e}", e=error)
        raise HTTPException(
            status_code=500, detail=f"Error during template pre-processing: {error}"
        )

    return TemplateResponse(
        content=text,
        template_type=template_type,
        template_version=ver,
    )


async def get_template_instructions(
    template_type: str,
    version: str,
    app_root_url: str,
    artifact_name: str | None = None,
    server_mode_kind: ServerModeKind = ServerModeKind.API,
) -> TemplateInstructionsResponse:
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        logger.error(
            "Version validation failed: {v_result_error}", v_result_error=v_result.error
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_result.error)
        )
    ver = v_result.data
    path = _TEMPLATE_DIR / template_type / ver / "instructions.md"
    if not path.exists():
        logger.error("Instructions file not found at path: {path}", path=path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Instructions file not found."
        )
    fm = FrontMatterMeta(file_path=path)

    if artifact_name is None:
        has_artifact_name = False
        artifact_name = "{Artifact Name}"
    else:
        has_artifact_name = True

    # process Jinja2 template
    cbib_ver = _SETTINGS.template_cbib_api.version

    if server_mode_kind == ServerModeKind.API:
        link_block = f"""📘 **API Definition:**  
[`{_API_RELATIVE_URL}/executor_modes/CANONICAL-EXECUTOR-MODE-V{cbib_ver}`]({app_root_url}/executor_modes/CANONICAL-EXECUTOR-MODE-V{cbib_ver})"""
    else:
        link_block = f"""📘 **MCP Definition:**

- Resource Name: `template_executor_mode`
- Resource URI: `executor-mode://executor_mode/{cbib_ver}`"""

    if artifact_name:
        template_scope_block = (
            f"**Template application scope:** `artifact_name: {artifact_name}`  "
        )
    else:
        template_scope_block = ""

    template: Template = Template(source=fm.content)
    content = template.render(
        link_definition_block=link_block,
        artifact_name=artifact_name,
        template_scope_block=template_scope_block,
    )

    fm.content = content

    if fm.has_field("canonical_executor_mode"):
        if server_mode_kind == ServerModeKind.API:
            fm.frontmatter["canonical_executor_mode"]["api_path"] = (
                f"{app_root_url}/executor_modes/CANONICAL-EXECUTOR-MODE-V{fm.frontmatter['canonical_executor_mode']['version']}"
            )
        elif server_mode_kind == ServerModeKind.MCP:
            fm.frontmatter["canonical_executor_mode"]["resource_uri"] = (
                f"executor-mode://executor_mode/{cbib_ver}"
            )
            fm.frontmatter["canonical_executor_mode"]["resource_name"] = (
                "template_executor_mode"
            )

    if fm.has_field("template_registry"):
        if server_mode_kind == ServerModeKind.API:
            fm.frontmatter["template_registry"]["api_path"] = (
                f"{app_root_url}/{_TEMPLATE_DIR.name}/{template_type}/{ver}/registry"
            )
        elif server_mode_kind == ServerModeKind.MCP:
            fm.frontmatter["template_registry"]["mcp_tool_name"] = (
                "get_template_registry"
            )

    if fm.has_field("template_info"):
        if server_mode_kind == ServerModeKind.API:
            fm.frontmatter["template_info"]["api_path"] = (
                f"{app_root_url}/{_TEMPLATE_DIR.name}/{template_type}/{ver}"
            )
        elif server_mode_kind == ServerModeKind.MCP:
            fm.frontmatter["template_info"]["mcp_tool_name"] = "get_template"

    text = fm.get_template_text()
    if has_artifact_name:
        text = text.replace("{Artifact Name}", artifact_name)

    return TemplateInstructionsResponse(
        content=text,
        template_type=template_type,
        template_version=ver,
    )


async def get_template_registry(
    template_type: str,
    version: str,
    monad_name: str | None = None,
    server_mode_kind: ServerModeKind = ServerModeKind.API,
) -> dict[str, Any]:
    reg = _get_template_registry(template_type, version)

    try:
        if monad_name:
            pre_processor = PreProcessRegistry(registry=reg, monad_name=monad_name)
            processed_reg = pre_processor.pre_process_registry()
            logger.debug(
                "Processed registry with monad: {monad_name}", monad_name=monad_name
            )
            return processed_reg
        logger.debug("No monad name found in session for registry pre-processing.")
    except Exception as error:
        logger.error("Error during registry pre-processing: {e}", e=error)
        raise HTTPException(
            status_code=500, detail=f"Error during registry pre-processing: {error}"
        )
    return reg


async def get_template_status(
    template_type: str,
    version: str,
    server_mode_kind: ServerModeKind = ServerModeKind.API,
) -> TemplateStatusResponse:
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        logger.error(
            "Version validation failed: {v_result_error}", v_result_error=v_result.error
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_result.error)
        )
    ver = v_result.data
    dt_now = datetime.now().astimezone()
    status_dict = {
        "status": "available",
        "template_type": template_type,
        "template_version": ver,
        "template": "available",
        "registry": "available",
        "manifest": "available",
        "instructions": "available",
        "last_verified": dt_now,
    }

    return TemplateStatusResponse(**status_dict)


async def get_template_manifest(
    template_type: str,
    version: str,
    app_root_url: str,
    server_mode_kind: ServerModeKind = ServerModeKind.API,
) -> ManifestResponse:
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        logger.error(
            "Version validation failed: {v_result_error}", v_result_error=v_result.error
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_result.error)
        )
    ver = v_result.data
    results_dict = _get_template_manifest(
        template_type, ver, app_root_url, server_mode_kind=server_mode_kind
    )
    manifest = ManifestResponse(**results_dict)
    return manifest


def _verify_artifact(submission: ArtifactSubmission) -> VerifyArtifactResponse:
    content = submission.template_content.strip()
    if not content:
        logger.error("Template frontmatter is empty.")
        raise HTTPException(
            status_code=400, detail="Template frontmatter cannot be empty."
        )

    fm = FrontMatterMeta.from_content(content)
    if not fm.template_type:
        logger.error("Field template_type is not specified in frontmatter.")
        raise HTTPException(
            status_code=400,
            detail="Field template_type is not specified in frontmatter.",
        )

    if not fm.template_version:
        logger.error("Field template_version is not specified in frontmatter.")
        raise HTTPException(
            status_code=400,
            detail="Field template_version is not specified in frontmatter.",
        )

    registry_path = (
        _TEMPLATE_DIR / fm.template_type / f"v{fm.template_version}" / "registry.json"
    )
    if not registry_path.is_absolute():
        registry_path = Path.cwd() / registry_path
    if not registry_path.exists():
        logger.error(
            "No registry found for template_type: {template_type}, template_version: {template_version}",
            template_type=fm.template_type,
            template_version=fm.template_version,
        )
        raise HTTPException(
            status_code=400,
            detail=f"No registry found for the specified template_type of {fm.template_type} and template_version {fm.template_version} not found.",
        )
    registry: dict[str, Any] = json.loads(registry_path.read_text())

    verify_instance = VerifyMetaFields(registry=registry, fm=fm)
    result = verify_instance.verify()
    if not result.is_success:
        logger.error("Template verification failed: {error}", error=result.error)
        raise HTTPException(
            status_code=500,
            detail=str(result.error),
        )

    dt_now = datetime.now().astimezone()
    default_result = {
        "status": 200,
        "template_type": fm.template_type,
        "template_id": fm.template_id,
        "template_version": fm.template_version,
        "registry_id": registry.get("registry_id"),
        "registry_version": registry.get("registry_version"),
        "field_validation": "pass",
        "verified_at": dt_now.isoformat(),
    }

    data = result.data
    if not data:
        raise HTTPException(
            status_code=500,
            detail="Verification result data is missing.",
        )
    errors: list[str] = []
    if "missing_fields" in data and data["missing_fields"]:
        errors.append("missing fields")
        default_result["status"] = status.HTTP_422_UNPROCESSABLE_ENTITY
        default_result["field_validation"] = "failed"
        default_result["missing_fields"] = data["missing_fields"]
    if "extra_fields" in data and data["extra_fields"]:
        default_result["extra_fields"] = data["extra_fields"]
    if "incorrect_type_fields" in data and data["incorrect_type_fields"]:
        errors.append("incorrect type fields")
        default_result["status"] = status.HTTP_422_UNPROCESSABLE_ENTITY
        default_result["field_validation"] = "failed"
        default_result["incorrect_type_fields"] = data["incorrect_type_fields"]
    if "rule_errors" in data and data["rule_errors"]:
        errors.append("rule errors")
        default_result["status"] = status.HTTP_422_UNPROCESSABLE_ENTITY
        default_result["field_validation"] = "failed"
        default_result["rule_errors"] = data["rule_errors"]

    try:
        result = VerifyArtifactResponse(**default_result)
    except ValidationError as e:
        logger.error("Validation error in VerifyArtifactResponse: {error}", error=e)
        raise HTTPException(
            status_code=500,
            detail=f"Validation error in VerifyArtifactResponse: {e}",
        )
    if result.status != status.HTTP_200_OK:
        details = {"message": "Template verification failed.", "errors": errors}
        model_details = result.model_dump(
            exclude={
                "status",
                "template_api_path",
                "registry_api_path",
                "manifest_api_path",
                "instructions_api_path",
            }
        )
        details.update(model_details)
        logger.error("Template verification failed.")
        raise HTTPException(
            status_code=result.status,
            detail=details,
        )

    return result


async def verify_mcp_artifact(
    submission: ArtifactSubmission,
) -> VerifyArtifactMcpResponse:
    artifact_response = _verify_artifact(submission)
    default_result = artifact_response.model_dump()
    return VerifyArtifactMcpResponse(**default_result)


async def verify_api_artifact(
    submission: ArtifactSubmission,
    app_root_url: str,
) -> VerifyArtifactApiResponse:
    artifact_response = _verify_artifact(submission)
    default_result = artifact_response.model_dump()
    template_api_path = f"{app_root_url}/{_TEMPLATE_DIR}/{artifact_response.template_type}/v{artifact_response.template_version}"

    default_result["template_api_path"] = template_api_path
    default_result["registry_api_path"] = f"{template_api_path}/registry"
    default_result["manifest_api_path"] = f"{template_api_path}/manifest"
    default_result["instructions_api_path"] = f"{template_api_path}/instructions"
    return VerifyArtifactApiResponse(**default_result)


async def finalize_artifact(
    submission: ArtifactSubmission,
    server_mode_kind: ServerModeKind = ServerModeKind.API,
) -> FinalizeArtifactResponse:
    content = submission.template_content.strip()
    if not content:
        logger.error("Template frontmatter is empty.")
        raise HTTPException(
            status_code=400, detail="Template frontmatter cannot be empty."
        )
    fm = FrontMatterMeta.from_content(content)
    if not fm.template_type:
        logger.error("Field template_type is not specified in frontmatter.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field template_type is not specified in frontmatter.",
        )

    if not fm.template_version:
        logger.error("Field template_version is not specified in frontmatter.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field template_version is not specified in frontmatter.",
        )

    registry_path = (
        _TEMPLATE_DIR / fm.template_type / f"v{fm.template_version}" / "registry.json"
    )
    if not registry_path.is_absolute():
        registry_path = Path.cwd() / registry_path
    if not registry_path.exists():
        logger.error(
            f"No registry found for template_type: {fm.template_type}, template_version: {fm.template_version}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No registry found for the specified template_type of {fm.template_type} and template_version {fm.template_version} not found.",
        )
    registry: dict[str, Any] = json.loads(registry_path.read_text())

    clean_instance = CleanMetaFields(registry=registry, fm=fm)
    result = clean_instance.cleanup()

    default_result = {
        "content": result.get_template_text(),
        "status": status.HTTP_200_OK,
    }

    try:
        finalize_result = FinalizeArtifactResponse(**default_result)
    except ValidationError as e:
        logger.error("Validation error in FinalizeArtifactResponse: {error}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error in FinalizeArtifactResponse: {e}",
        )
    return finalize_result


def _upgrade_to_template(
    submission: UpgradeToTemplateSubmission,
    app_root_url: str,
    server_mode_kind: ServerModeKind = ServerModeKind.API,
) -> UpgradeArtifactResponse:
    contents = submission.markdown_content.strip()
    if not contents:
        logger.error("Template contents are empty.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template contents cannot be empty.",
        )

    try:
        upgrade_fm = FrontMatterMeta.from_content(contents)
    except Exception as e:
        logger.error("Error parsing template contents: {error}", error=e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing template contents: {e}",
        )

    v_result = _validate_version_str(submission.new_version)
    if Result.is_failure(v_result):
        if isinstance(
            v_result.error, (VersionLatestError, VersionNoneError, VersionEmptyError)
        ):
            versions = fn_versions.get_available_versions().templates
            latest_version = versions.get(upgrade_fm.template_type)
            if not latest_version:
                logger.error(
                    "No available versions found for template_type: {template_type}",
                    template_type=upgrade_fm.template_type,
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No available versions found for template_type: {upgrade_fm.template_type}",
                )
            latest_version_for_template = fn_versions.get_latest_version_for_template(
                upgrade_fm.template_type
            )
            if latest_version_for_template is None:
                upgrade_fm.template_version = ""
            else:
                submission.new_version = latest_version_for_template
                upgrade_fm.template_version = latest_version_for_template

    v_result = _validate_version_str(submission.new_version)
    if not Result.is_success(v_result):
        logger.error(
            "Version validation failed: {v_result_error}", v_result_error=v_result.error
        )
        raise HTTPException(status_code=400, detail=str(v_result.error))
    new_version = v_result.data

    if not upgrade_fm.template_type:
        logger.error("Field template_type is not specified in frontmatter.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field template_type is not specified in frontmatter.",
        )

    try:
        path = _TEMPLATE_DIR / upgrade_fm.template_type / new_version / "template.md"
        if not path.exists():
            logger.error("Template file not found at path: {path}", path=path)
            raise HTTPException(status_code=404, detail="Template file not found.")
        template_fm = FrontMatterMeta(file_path=path)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error loading template for type {upgrade_fm.template_type} and version {new_version}: {e}",
        )

    try:
        upgrade_template = UpgradeTemplate(
            upgrade_fm=upgrade_fm, template_fm=template_fm
        )
        upgraded_dict = upgrade_template.apply_upgrade()
        upgraded_fm: FrontMatterMeta = upgraded_dict["frontmatter"]
        extra_fields = upgraded_dict["extra_fields"]
    except Exception as e:
        logger.error("Error applying upgrade: {error}", error=e)
        raise HTTPException(
            status_code=500,
            detail=f"Error applying upgrade: {e}",
        )

    dt_now = datetime.now().astimezone()
    result = {
        "status": status.HTTP_200_OK,
        "template_type": upgrade_fm.template_type,
        "template_id": upgrade_fm.template_id,
        "template_version": new_version,
        "requires_field_being": True,
        "content": upgraded_fm.get_template_text(),
        "content_media_type": "text/markdown",
        "content_has_front_matter": True,
        "artifact_name": submission.artifact_name.strip(),
        "upgraded_at": dt_now.isoformat(),
        "extra_fields": extra_fields,
    }

    try:
        upgrade_result = UpgradeArtifactMcpResponse(**result)
    except ValidationError as e:
        logger.error("Validation error in UpgradeArtifactResponse: {error}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error in UpgradeArtifactResponse: {e}",
        )

    return upgrade_result


async def upgrade_to_api_template(
    submission: UpgradeToTemplateSubmission,
    app_root_url: str,
    server_mode_kind: ServerModeKind = ServerModeKind.API,
) -> UpgradeArtifactApiResponse:
    try:
        artifact_response = _upgrade_to_template(
            submission, app_root_url, server_mode_kind=server_mode_kind
        )
        mcp_result_model = UpgradeArtifactApiResponse.from_artifact_response(
            artifact_response
        )
        mcp_result = mcp_result_model.model_dump()

        manifest = _get_template_manifest(
            mcp_result_model.template_type,
            mcp_result_model.template_version,
            app_root_url,
            server_mode_kind=server_mode_kind,
        )

        manifest_fields = {
            "template_api_path",
            "registry_api_path",
            "manifest_api_path",
            "instructions_api_path",
            "executor_mode_api_path",
        }
        for field in manifest_fields:
            if field in manifest:
                mcp_result[field] = manifest[field]
        upgrade_result = UpgradeArtifactApiResponse(**mcp_result)
    except ValidationError as e:
        logger.error("Error in UpgradeArtifactApiResponse: {error}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error in UpgradeArtifactApiResponse: {e}",
        )

    return upgrade_result


async def upgrade_to_mcp_template(
    submission: UpgradeToTemplateSubmission,
    app_root_url: str,
    server_mode_kind: ServerModeKind = ServerModeKind.API,
) -> UpgradeArtifactMcpResponse:
    try:
        artifact_response = _upgrade_to_template(
            submission, app_root_url, server_mode_kind=server_mode_kind
        )

        upgrade_result = UpgradeArtifactMcpResponse.from_artifact_response(
            artifact_response
        )
    except ValidationError as e:
        logger.error("Error in UpgradeArtifactMcpResponse: {error}", error=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error in UpgradeArtifactMcpResponse: {e}",
        )

    return upgrade_result
