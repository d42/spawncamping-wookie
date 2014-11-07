from webkimono.kimono import KimonoApi
from webkimono.appexceptions import NotKimonoException
from urllib import parse


class KimonoCache:
    def __init__(self):
        self.all_kimonos = {}
        pass

    def get(self, kimono_url):
        key = self.to_key(kimono_url)
        return self.all_kimonos.get(key, None)

    def set(self, kimono_url, kimono):
        key = self.to_key(kimono_url)
        if not isinstance(kimono, KimonoApi):
            raise NotKimonoException
        self.all_kimonos[key] = kimono

    @staticmethod
    def to_key(kimono_url):
        return parse.urlparse(kimono_url).path

    def __contains__(self, kimono_url):
        return self.get(kimono_url)

cache = KimonoCache()
