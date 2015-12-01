# statsdmiddleware
Repo with an example Flask app which uses my statsd middleware.

# setup

    $ make bootstrap

This will setup the virtualenv and requirements (Flask and dogstatsd-python).


# running

    $ make run

This will run the built-in flask webserver in debug mode.  Afterwards you can
open `http://127.0.0.1:5000/test` to trigger a rendering of the `test` view.


# seeing metrics

    $ make tcpdump

This runs tcpdump so you can see the UDP packets containing the statsd metrics
the middleware is emitting.  For a proper experience I recommend getting setup
with <a href="https://www.datadoghq.com/">Datadog</a> and passing your metrics
there ;-)
