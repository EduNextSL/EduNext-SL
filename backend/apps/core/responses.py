"""Success envelope shared by every endpoint: {"success": true, "message"?, "data"}."""

from typing import Any

from rest_framework import status as http
from rest_framework.response import Response


def success_response(
    data: Any = None, *, message: str | None = None, status: int = http.HTTP_200_OK
) -> Response:
    body: dict[str, Any] = {"success": True}
    if message:
        body["message"] = message
    body["data"] = {} if data is None else data
    return Response(body, status=status)
