import json
import os

from collections import defaultdict
from functools import wraps
from itertools import zip_longest
from urllib import parse

from kimono import KimonoApi, correlate, trim
from flask import Flask, render_template, request, session, flash

app = Flask(__name__)
try:
    import application_settings
    app.config['SECRET'] = application_settings.secret
except ImportError:
        app.config['SECRET'] = os.urandom(64)

all_kimonos = {}
user_kimonos = defaultdict(set)



def assure_session(func):

    @wraps(func)
    def inner():
        if 'session_id' not in session:
            session['session_id'] = os.urandom(64)
        return func()
    return inner


@app.route('/')
def start():
    return render_template('index.html')


def tabularize(kimonos):
    headers = [(k.name, len(k.collections)) for k in kimonos]
    collections = [cname for k in kimonos for cname in k.collections]
    columns = [
            [[k.name, collection, property] for collection, properties in k.properties.items()
                                                    for property in properties]
               for k in kimonos
    ]

    rows = list(zip_longest(*columns))
    return headers, collections, rows



def kimonos_from_urls(urls):
    for url in urls:
        parsed_url = parse.urlparse(url)
        if parsed_url.netloc != 'kimonolabs.com':
            flash("{} is not legal kimonolabs.com link!".format(url))
            continue

        if url not in all_kimonos:
            all_kimonos[url] = KimonoApi(url)
        yield all_kimonos[url]

@app.route('/select', methods=['POST', 'GET'])
@assure_session
def select():
    s_id = session['session_id']

    if request.method == 'POST':
        urls = (u for u in request.form['urls'].split('\n') if u)
        url_kimonos = list(kimonos_from_urls(urls))
        user_kimonos[s_id] |= set(url_kimonos)

    headers, collections, rows = tabularize(list(user_kimonos[s_id]))

    return render_template('select.html',
                           rows=rows,
                           headers=headers,
                           collections=collections)


@app.route('/discover')
@assure_session
def discover():
    return render_template('discover.html')


@app.route('/graph', methods=['POST'])
@assure_session
def graph():
    s_id = session['session_id']
    properties = [e[len('property_'):] for e in request.form.keys()
                  if e.startswith('property_')]

    resolutions = ['D', '12H', 'H', '30Min', '15Min']
    resolution = resolutions[int(request.form['resolution'])]

    def extract_kimonoapi(string):
        kname, cname, pname = string.split('.')
        kimono = next(k for k in user_kimonos[s_id] if k.name == kname)
        return kimono.get_property(cname, pname, resolution)

    herp, derp = map(extract_kimonoapi, properties)
    herp, derp = trim(herp, derp)
    cor = correlate(herp, derp)
    dates = [int(d.strftime('%s')) for d in herp.index]

    p1 = [{'x': d, 'y': v} for d, v in zip(dates, list(herp.values))]
    p2 = [{'x': d, 'y': v} for d, v in zip(dates, list(derp.values))]
    return render_template('stat.html',
                           points=json.dumps([p1, p2]),
                           correlation=cor, s1_name=herp.name, s2_name=derp.name)

if __name__ == "__main__":
    app.debug = True
    app.config['SECRET_KEY'] = 'penis'
    app.run()
