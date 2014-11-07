from flask import Flask
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

import webkimono.views
