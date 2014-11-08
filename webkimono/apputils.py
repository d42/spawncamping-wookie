import os

from functools import wraps
from itertools import zip_longest
from urllib import parse

from flask import session, flash, url_for, redirect

from webkimono.caching import cache
from webkimono.kimono import KimonoApi
from webkimono.appexceptions import InvalidUsage
def assure_session(func):

    @wraps(func)
    def inner():
        if 'session_id' not in session:
            session['session_id'] = os.urandom(64)
        return func()
    return inner


def tabularize(kimonos):
    headers = [(k.name, len(k.collections)) for k in kimonos]
    collections = [cname for k in kimonos for cname in k.collections]
    columns = []
    for k in kimonos:

        columns.append(
            [[k.name, colec, prop] for colec, props in k.properties.items()
            for prop in props]
        )

    rows = list(zip_longest(*columns))
    return headers, collections, rows


def kimonos_from_urls(urls):
    for url in urls:
        parsed_url = parse.urlparse(url)
        if parsed_url.netloc not in ['kimonolabs.com', 'www.kimonolabs.com']:
            flash("{} is not legal kimonolabs.com link!".format(url))
            continue

        api_path = parsed_url.path
        api_key = parse.parse_qs(parsed_url.query).get('apikey', None)
        if not api_key:
            flash("{} does not contain api key!".format(url))
            continue

        api_key = api_key[0]

        query = parse.urlencode({'apikey': api_key, 'kimseries': 1})

        final_url = parse.urlunparse(['https', 'www.kimonolabs.com', api_path, '', query, ''])

        if final_url not in cache:
            cache.set(final_url, KimonoApi(final_url))
        yield cache.get(final_url)


def read_select_form(form):
    def read(value, table, error):
        try:
            return table[int(value)]
        except:
            InvalidUsage(error)

    properties = [e[len('property_'):] for e in form.keys()
                  if e.startswith('property_')]

    if len(properties) != 2:
        raise InvalidUsage("can haz 2 properties")


    resolutions = ['D', '12H', 'H', '30Min', '15Min']
    resamplings = ['mean', 'max', 'sum']
    missings = ['mean', '0', 'ignore']

    resolution = read(form["resolution"], resolutions, "resolution out of bound")
    resampling = read(form["resamplingmethods"], resamplings, "resampling out of bound")
    missing = read(form["missingmethods"], missings, "missing methods out of bound")

    return properties, resolution, resampling, missing

