from elasticsearch import Elasticsearch

from app.config import settings


class ESClient:
    def __init__(self):
        self.xml_path = settings.RAW_XML_PATH
        self.host = settings.ES_HOST
        self.port = settings.ES_PORT
        self.index = settings.ES_INDEX
        self.user = settings.ES_USER
        self.password = settings.ES_PASSWORD
        self.engine = Elasticsearch(
            [{"host": self.host, "port": self.port, "scheme": "http"}],
            basic_auth=(self.user, self.password.get_secret_value())
            if self.user and self.password
            else None,
            request_timeout=120,
        )
