from fastapi.responses import Response


class MarkdownResponse(Response):
    media_type = "text/markdown"
