"""This module defines the health blueprint factory."""

from flask import Blueprint, jsonify

from src.interactor.use_cases.health.health_use_case import HealthUseCase


def create_health_bp(health_use_case: HealthUseCase = None, version: str = "v1"):
    bp = Blueprint("health_v1", __name__, url_prefix=f"/api/{version}")

    @bp.get("/health")
    def health():
        result = health_use_case.execute()
        return jsonify(result), 200 if result["status"] == "ok" else 500

    return bp
