"""Users blueprint exposing create, get and list."""

from flask import Blueprint, request

from src.interactor.use_cases.users.users_use_case import UsersUseCase


def users_bp(users_use_case: UsersUseCase, version: str = "v1"):
    bp = Blueprint("users_v1", __name__, url_prefix=f"/api/{version}/users")

    @bp.post("")
    def create_user():
        payload = request.get_json(force=True)
        return users_use_case.create(payload)

    @bp.get("/<string:uid>")
    def get_user(uid: str):
        return users_use_case.get(uid)

    @bp.get("")
    def list_users():
        return users_use_case.list(**request.args.to_dict())

    return bp
