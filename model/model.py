import logging
from typing import Any, Dict, Tuple

from flask import Flask, jsonify, request

#from model.agent_workflow import react_workflow

logger = logging.getLogger(__name__)


def _execute_workflow(payload: Dict[str, Any]):
    chat_id = payload["chat_id"]
    user_request = payload["user_request"]
    logger.debug("Executing workflow for chat_id=%s", chat_id)
    # workflow_result = react_workflow(chat_id, user_request)
    workflow_result = "mock mesage with {user_request}"
    return jsonify({"message": f"mock-данные от model\nТело запроса: {workflow_result}"})


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
