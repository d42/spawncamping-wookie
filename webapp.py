import json

from collections import defaultdict

from flask import Flask, render_template, request, session, flash, redirect, url_for

from apputils import assure_session, kimonos_from_urls, tabularize
from kimono import KimonoApi, correlate, trim, PropertyNotFoundException
from caching import cache

app = Flask(__name__)
try:
    import application_settings
    app.config['SECRET_KEY'] = application_settings.secret
except ImportError:
    import os
    app.config['SECRET_KEY'] = os.urandom(64)

import logging
from logging import FileHandler
handler = FileHandler("kimono.log")
app.logger.setLevel(logging.WARNING)
app.logger.addHandler(handler)

user_kimonos = defaultdict(set)


@app.route('/')
def start():
    return render_template('index.html')


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


@app.route('/graph', methods=['POST', 'GET'])
@assure_session
def graph():
    s_id = session['session_id']
    properties = [e[len('property_'):] for e in request.form.keys()
                  if e.startswith('property_')]


    if len(properties) != 2 or request.method == 'GET':
        flash("can haz 2 properties")
        return redirect(url_for('discover'))

    resolutions = ['D', '12H', 'H', '30Min', '15Min']
    resolution = resolutions[int(request.form['resolution'])]

    def extract_kimonoapi(string):
        kname, cname, pname = string.split('.')
        kimono = next(k for k in user_kimonos[s_id] if k.name == kname)
        try:
            return kimono.get_property(cname, pname, resolution)
        except TypeError:
            app.logger.error(kimono.content)
    try:
        herp, derp = map(extract_kimonoapi, properties)
    except PropertyNotFoundException:
        flash("Something went wrong! property not found!")
        return start()

    herp, derp = trim(herp, derp)
    cor = correlate(herp, derp)
    dates = [int(d.strftime('%s')) for d in herp.index]

    p1 = [{'x': d, 'y': v} for d, v in zip(dates, list(herp.values))]
    p2 = [{'x': d, 'y': v} for d, v in zip(dates, list(derp.values))]
    return render_template('stat.html',
                           points=json.dumps([p1, p2]),
                           correlation=cor, s1_name=herp.name, s2_name=derp.name)

if ( app.debug ):
    from werkzeug.debug import DebuggedApplication
    app.wsgi_app = DebuggedApplication( app.wsgi_app, True )

if __name__ == "__main__":
    app.debug = True
    app.config['SECRET_KEY'] = 'penis'
    app.run()
