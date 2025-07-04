from requests import PreparedRequest
from requests.structures import CaseInsensitiveDict
from requests.auth import AuthBase


class BearerAuth(AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r: PreparedRequest):
        r.headers = r.headers or CaseInsensitiveDict()
        r.headers["Authorization"] = "Bearer " + self.token
        return r
