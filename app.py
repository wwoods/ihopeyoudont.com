import datetime
from flask import (flash, Flask, get_flashed_messages, render_template,
        redirect, request, url_for)
import hashlib
import pymongo
from smail import send_mail
import threading
import time

app = Flask(__name__)
app.config.from_pyfile('app.config')
try:
    app.config.from_pyfile('app.local.config')
except IOError:
    pass

app.jinja_env.add_extension('pyjade.ext.jinja.PyJadeExtension')
body = """And right now, {frm} is hoping you don't {action}.  Please rest
peacefully, now that you know this.

Thank you,
ihopeyoudont.com"""


c = None
def initDb():
    global c
    c = pymongo.Connection(host = app.config['MONGO_HOST'],
            port = app.config['MONGO_PORT'])[app.config['MONGO_DATABASE']]


requestsBase = [ time.time() ]
requestsLeft = [ app.config['MAX_PER_HOUR'] ]
requestsTimeEach = 3600.0 / requestsLeft[0]
requestsLock = threading.Lock()
def throttleTest():
    """Return True if we can send and increment counter; false otherwise."""
    with requestsLock:
        # Regenerate requests
        step = time.time() - requestsBase[0]
        requestsBase[0] += step
        requestsLeft[0] += step / requestsTimeEach
        if requestsLeft[0] >= 1:
            requestsLeft[0] -= 1
            return True
        return False


@app.route('/')
def welcome():
    return render_template("main.jade")


@app.route('/submit', methods=[ "POST" ])
def submit():
    email, action = request.form['email'], request.form['action']
    frm = request.form['from']
    if len(frm) > 40:
        flash("From field too long... did you cheat the browser?")
        return redirect(url_for('welcome'))
    if len(email) > 60:
        flash("Destination e-mail field too long... did you cheat the browser?")
        return redirect(url_for('welcome'))
    if len(action) > 80:
        flash("Action field too long... did you cheat the browser?")
        return redirect(url_for('welcome'))

    if not email.endswith('@example.com'):
        if throttleTest():
            send_mail(app, email, "{0} has hope".format(frm),
                    body.format(frm = frm, action = action))
            c['sent'].insert({ 'from': hashlib.sha1(frm).hexdigest(),
                    'to': hashlib.sha1(email).hexdigest(),
                    'msg': action,
                    'tsSent': datetime.datetime.utcnow() })
        else:
            now = datetime.datetime.utcnow().strftime("%Y%m%d")
            c['throttling'].update({ '_id': 'throttles-' + now },
                    { '$inc': { 'count': 1 } }, upsert = True)
            flash("Failed to send; throttling exceeded")
            return redirect(url_for('welcome'))

    flash(email, category = "email")
    return redirect(url_for('accepted'))


@app.route('/ok')
def accepted():
    email = get_flashed_messages(category_filter = "email")
    if email:
        email = email[0]
    else:
        email = 'someone'
    return render_template("accepted.jade", email = email)


if __name__ == '__main__':
    initDb()
    app.run(port = app.config['PORT'])

