import logging
from typing import Any, Dict, List, Mapping, Tuple

from flask import Flask, jsonify, request

from model.agent_workflow import react_workflow

logger = logging.getLogger(__name__)


def _execute_workflow(payload: Dict[str, Any]):
    chat_id = payload["chat_id"]
    messages: List[Mapping[str, Any]] = payload["messages"]
    messages = [*messages, {"role": "user", "content": payload["user_request"]}]
    logger.debug("Executing workflow for chat_id=%s", chat_id)
    workflow_result = react_workflow(chat_id, messages)
    message = workflow_result.get("message", "")
    is_support_needed = bool(workflow_result.get("is_support_needed", False))
    return jsonify({"message": message, "is_support_needed": is_support_needed})


def create_app() -> Flask:
    """Application factory for the model workflow service."""
    app = Flask(__name__)

    @app.route("/ping", methods=["GET"])
    def ping() -> Tuple[str, int]:
        return "", 200

    @app.route("/workflow", methods=["POST"])
    def workflow():
        payload = request.get_json(silent=True) or {}
        return _execute_workflow(payload)

    @app.route("/mock", methods=["POST"])
    def mock():
        payload = request.get_json(silent=True) or {}
        return _execute_workflow(payload)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
