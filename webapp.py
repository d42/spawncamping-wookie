from kimono import KimonoApi, correlate, trim, url1, url2
from flask import Flask, render_template
import json
app = Flask(__name__)

s1, s2 = [KimonoApi(url).get_any() for url in [url1, url2]]


@app.route("/")
def hello():

    cor = correlate(s1, s2)
    herp, derp = trim(s1, s2)
    dates = [int(d.strftime('%s')) for d in herp.index]

    p1 = [{'x': d, 'y': v} for d, v in zip(dates, list(herp.values))]
    p2 = [{'x': d, 'y': v} for d, v in zip(dates, list(derp.values))]
    return render_template('stat.html',
                           points=json.dumps([p1, p2]),
                           correlation=cor, s1_name=s1.name, s2_name=s2.name)

if __name__ == "__main__":
    app.debug = True
    app.run()
