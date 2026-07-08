from typing import Any, Optional, Tuple
from flask import Response, jsonify


class SuccessResponse:
    def __init__(
        self,
        data: Any = None,
        message: str = "Success",
        meta: Optional[dict[str, Any]] = None,
        status_code: int = 200
    ) -> None:
        self.data = data
        self.message = message
        self.meta = meta
        self.status_code = status_code

    def write_response(self) -> Tuple[Response, int]:
        response: dict[str, Any] = {
            "message": self.message,
            "data": self.data
        }

        if self.meta is not None:
            response["meta"] = self.meta

        return jsonify(response), self.status_code
