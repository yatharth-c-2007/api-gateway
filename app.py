"""
api-gateway
The only service meant to be reachable from outside the cluster
(everything else is internal-only, cluster-DNS reachable). Forwards
order-related requests to order-service. Deliberately thin — its
job is to be the single ingress point the mesh/ingress config
targets, not to contain business logic.
"""
from flask import Flask, jsonify, request
import os
import logging
import requests

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-gateway")

ORDER_SERVICE_URL = os.environ.get("ORDER_SERVICE_URL", "http://localhost:5003")
REQUEST_TIMEOUT = float(os.environ.get("DOWNSTREAM_TIMEOUT_SECONDS", "5"))


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", service="api-gateway"), 200


@app.route("/api/orders", methods=["POST"])
def create_order():
    try:
        resp = requests.post(
            f"{ORDER_SERVICE_URL}/orders",
            json=request.get_json(silent=True) or {},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.RequestException as exc:
        logger.error("order-service call failed: %s", exc)
        return jsonify(error="order service unavailable"), 503

    return (resp.text, resp.status_code, {"Content-Type": "application/json"})


@app.route("/api/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    try:
        resp = requests.get(f"{ORDER_SERVICE_URL}/orders/{order_id}", timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        logger.error("order-service call failed: %s", exc)
        return jsonify(error="order service unavailable"), 503

    return (resp.text, resp.status_code, {"Content-Type": "application/json"})


@app.route("/api/orders", methods=["GET"])
def list_orders():
    try:
        resp = requests.get(f"{ORDER_SERVICE_URL}/orders", timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        logger.error("order-service call failed: %s", exc)
        return jsonify(error="order service unavailable"), 503

    return (resp.text, resp.status_code, {"Content-Type": "application/json"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
