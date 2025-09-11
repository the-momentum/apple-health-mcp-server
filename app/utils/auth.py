from requests import PreparedRequest
from requests.auth import AuthBase
from requests.structures import CaseInsensitiveDict


class BearerAuth(AuthBase):
    """Attaches HTTP Bearer Authentication to the given Request object."""

    def __init__(self, token: str):
        self.token = token

    def __call__(self, r: PreparedRequest) -> PreparedRequest:
        r.headers = r.headers or CaseInsensitiveDict()
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r
