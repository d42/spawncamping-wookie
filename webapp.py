import json
import os

from collections import defaultdict
from functools import wraps
from itertools import zip_longest

from kimono import KimonoApi, correlate, trim
from flask import Flask, render_template, request, session

app = Flask(__name__)

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


@app.route('/select', methods=['POST', 'GET'])
@assure_session
def select():
    s_id = session['session_id']

    if request.method == 'POST':
        urls = request.form['urls'].split('\n')

        for url in urls:
            if url not in all_kimonos: all_kimonos[url] = KimonoApi(url)
            user_kimonos[s_id].add(all_kimonos[url])



    kimonos = list(user_kimonos[s_id])
    headers = [(k.name, len(k.collections)) for k in kimonos]
    collections = [cname for k in kimonos for cname in k.collections]
    columns = [
            [[k.name, collection, property] for collection, properties in k.properties.items()
                                                    for property in properties]
               for k in kimonos
    ]

    rows = list(zip_longest(*columns))


    return render_template('select.html', rows=rows, headers=headers,
                                          collections=collections)


@app.route('/graph', methods=['POST'])
@assure_session
def graph():
    s_id = session['session_id']
    def extract_kimonoapi(string):
        kname, cname, pname = string.split('.')
        kimono = next(k for k in user_kimonos[s_id] if k.name == kname)
        return kimono.get_property(cname, pname)

    herp, derp = map(extract_kimonoapi, request.form.keys())
    herp, derp = trim(herp, derp)
    cor = correlate(herp, derp)
    import ipdb; ipdb.set_trace()
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
