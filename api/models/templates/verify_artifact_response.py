from typing import Annotated, Optional
from pydantic import BaseModel, Field


class VerifyArtifactResponse(BaseModel):
    status: Annotated[
        int,
        Field(
            default=200,
            title="Status",
            description="Template Status: 200 for verified, or 422 for failed.",
        ),
    ] = 200
    template_type: Annotated[
        str,
        Field(
            description="Type of the template, e.g., 'glyph', 'sigil', etc.",
            max_length=255,
        ),
    ]

    template_id: Annotated[
        str,
        Field(
            default="",
            title="Template ID",
            description="Unique identifier for the template.",
        ),
    ] = ""

    template_version: Annotated[
        str,
        Field(
            title="Template Type",
            description="Version of the template, e.g., '1.0', '2.10', etc.",
        ),
    ]

    verified_at: Annotated[
        str,
        Field(
            title="Verified At",
            description="Timestamp when the artifact was verified.",
        ),
    ]

    field_validation: Annotated[
        str,
        Field(
            default="pass",
            title="Field Validation",
            description="Field Validation: 'pass' or 'failed'.",
        ),
    ] = "pass"

    registry_version: Annotated[
        Optional[str],
        Field(
            default=None,
            title="Registry Version",
            description="Version identifier for the registry.",
        ),
    ] = None

    missing_fields: Annotated[
        list[str],
        Field(
            default_factory=list,
            title="Missing Fields",
            description="List of missing fields found during verification.",
        ),
    ]

    incorrect_type_fields: Annotated[
        dict[str, dict[str, str]],
        Field(
            default_factory=dict,
            title="Incorrect Type Fields",
            description="Fields with incorrect types. Maps field names to a dictionary containing expected and actual types.",
        ),
    ]
    extra_fields: Annotated[
        list[str],
        Field(
            default_factory=list,
            title="Extra Fields",
            description="List of extra fields found during verification.",
        ),
    ]
    rule_errors: Annotated[
        list[str],
        Field(
            default_factory=list,
            title="Rule Errors",
            description="List of rule errors found during verification.",
        ),
    ]


class VerifyArtifactMcpResponse(VerifyArtifactResponse):
    @staticmethod
    def from_verify_artifact_response(
        response: VerifyArtifactResponse,
    ) -> "VerifyArtifactMcpResponse":
        """
        Static Method: Creates a VerifyArtifactMcpResponse instance from a VerifyArtifactResponse object.
        This method converts a VerifyArtifactResponse into a VerifyArtifactMcpResponse by
        dumping the model's data and unpacking it as keyword arguments to the constructor.

        Args:
            response (VerifyArtifactResponse): The response object to convert from.

        Returns:
            VerifyArtifactMcpResponse: The converted MCP response object.
        """

        return VerifyArtifactMcpResponse(**response.model_dump())


class VerifyArtifactApiResponse(VerifyArtifactResponse):
    template_api_path: Annotated[
        Optional[str],
        Field(
            default=None,
            title="Template API Path",
            description="API path for the template.",
        ),
    ] = None

    registry_api_path: Annotated[
        Optional[str],
        Field(
            default=None,
            title="Registry API Path",
            description="API path for the registry.",
        ),
    ] = None

    manifest_api_path: Annotated[
        Optional[str],
        Field(
            default=None,
            title="Manifest API Path",
            description="API path for the manifest.",
        ),
    ] = None

    instructions_api_path: Annotated[
        Optional[str],
        Field(
            default=None,
            title="Instructions API Path",
            description="API path for the instructions.",
        ),
    ] = None

    @staticmethod
    def from_verify_artifact_response(
        response: VerifyArtifactResponse,
    ) -> "VerifyArtifactApiResponse":
        """
        Static Method: Converts a VerifyArtifactResponse object into a VerifyArtifactApiResponse object.
        This method takes a VerifyArtifactResponse instance, dumps its model data,
        and uses it to instantiate a new VerifyArtifactApiResponse object.

        Args:
            response (VerifyArtifactResponse): The response object to be converted.

        Returns:
            VerifyArtifactApiResponse: The resulting API response object created from the input response.
        """

        return VerifyArtifactApiResponse(**response.model_dump())
