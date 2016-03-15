import os

from flask import Flask, render_template
from statsd import statsd as dogstatsd
from statsdmiddleware import StatsdMiddleware, StatsD


app = Flask("myapp")
app.config['statsd'] = StatsD(
    dogstatsd,
    tags=['app:{}'.format(app.name), 'stage:{}'.format(os.environ.get('RELEASE_STAGE', 'testing'))]
)
app.config['statsd'].connect(
    os.environ.get('DD_HOST', 'localhost'),
    os.environ.get('DD_PORT', 8125)
)
app.wsgi_app = StatsdMiddleware(app, app.config['statsd'], prefix='myapp')


@app.route('/test')
def test():
    # this will render fast..
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
