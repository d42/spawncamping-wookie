import json

from collections import defaultdict

from webkimono import app
from flask import render_template, request, session, flash, redirect, url_for

from webkimono.apputils import assure_session, kimonos_from_urls, tabularize, read_select_form
from webkimono.kimono import KimonoApi, correlate, trim, PropertyNotFoundException
from webkimono.caching import cache

from webkimono.appexceptions import InvalidUsage, UnknownError


user_kimonos = defaultdict(dict)


@app.errorhandler(InvalidUsage, UnknownError)
def on_invalid(error):
    return render_template('error.html', error=error)

@app.route('/')
def start():
    return render_template('index.html')


@app.route('/select', methods=['POST', 'GET'])
@assure_session
def select():
    s_id = session['session_id']

    if request.method == 'POST':
        urls = (u for u in request.form['urls'].split('\n') if u.strip())
        url_kimonos = list(kimonos_from_urls(urls))
        user_kimonos[s_id].update({k.name: k for k in url_kimonos})

    headers, collections, rows = tabularize(list(user_kimonos[s_id].values()))

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

    def extract_kimonoapi(string, resolution, how, na):
        kname, cname, pname = string.split('.')
        kimono = user_kimonos[s_id].get(kname, None)
        if not kimono:
            raise UnknownError("kimono extraction",
                               payload=[kname, user_kimonos[s_id]])

        try:
            series = kimono.get_property(cname, pname, resolution)
        except TypeError:
            raise UnknownError("get_property",
                               payload=[kimono.content, (cname, pname)])
        if na != 'ignore':
            series.fillna((series.mean() if na == 'mean' else 0), inplace=True)

        return series

    properties, res, how, na = read_select_form(request.form)

    herp, derp = (extract_kimonoapi(p, res, how, na) for p in properties)
    herp, derp = trim(herp, derp)
    cor = correlate(herp, derp)
    for series in [herp, derp]:
        if na == 'ignore':
            series.fillna(series.mean(), inplace=True)

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
