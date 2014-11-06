import json

from random import choice
from urllib import request
from datetime import datetime

import pandas
import matplotlib.pyplot as plt


class PropertyNotFoundException(Exception):
    pass

class KimonoApi:
    def __init__(self, url):
        self.url = url
        self.content = self.fetch(self.url)
        self.read_meta(self.content)

    def read_meta(self, content):
        self.name = content['name']
        self.count = content['count']
        self.collections = list(content['results'].keys())
        self.properties = {c_name: list(content['results'][c_name][0].keys())
                           for c_name in self.collections}

    def get_property(self, collection, property, resolution='D'):
        if collection not in self.collections or property not in self.properties[collection]:
            raise PropertyNotFoundException()

        entries = self.content['results'][collection][0][property]
        series = self.to_series(entries, resolution)
        series.name = '{}>{}'.format(collection, property)
        series = series.fillna(series.mean())
        return series

    def get_any(self):
        collection = choice(self.collections)
        property = choice(self.properties[collection])
        return self.get_property(collection, property)

    @staticmethod
    def fetch(url, encoding='utf-8'):
        return json.loads(request.urlopen(url).read().decode(encoding))

    @staticmethod
    def to_series(entries, resolution='D', time_format='%Y-%m-%dT%H:%M:%S.%fZ'):
        parsed_entries = sorted((datetime.strptime(e['d'], time_format), int(e['v']))
                                for e in entries)
        times, values = zip(*parsed_entries)
        return pandas.Series(values, times).resample(resolution)



def trim(s1, s2):
    begin = max(s1.index[0], s2.index[0])
    end = min(s1.index[-1], s2.index[-1])
    s2 = s2[begin:end]
    s1 = s1[begin:end]
    return s1, s2


def correlate(s1, s2):
    s1, s2 = trim(s1, s2)
    return s1.corr(s2, method='pearson')


def main():
    from stuff import url1, url2
    s1, s2 = [KimonoApi(url).get_any() for url in [url1, url2]]

    print(correlate(s1, s2))
    plt.show()

if __name__ == '__main__':
    main()
