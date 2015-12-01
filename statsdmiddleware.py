import inspect
from functools import partial
import re
import resource
import time


def get_cpu_time():
    resources = resource.getrusage(resource.RUSAGE_SELF)
    # add up user time (ru_utime) and system time (ru_stime)
    return resources[0] + resources[1]


class StatsD(object):
    '''
    A statsd wrapper object which automatically adds extra tags.
    '''
    overloaded_methods = ['timing', 'count', 'gauge', 'increment']

    def __init__(self, statsd, tags=None):
        self.statsd = statsd
        for name, method in inspect.getmembers(statsd, predicate=inspect.ismethod):
            if name in self.overloaded_methods:
                setattr(self, name, partial(self.wrapper, _orig=method))
            else:
                setattr(self, name, method)

        if tags is None:
            tags = []
        self.tags = tags

    def _merge_tags(self, tags):
        return [tag for tag in set(self.tags + tags)]

    def wrapper(self, *args, **kwargs):
        method = kwargs['_orig']
        del kwargs['_orig']

        if 'tags' in kwargs:
            kwargs['tags'] = self._merge_tags(kwargs['tags'])
        elif self.tags:
            kwargs['tags'] = self.tags

        return method(*args, **kwargs)


class TimingStats(object):
    def __init__(self, statsd, name=None, sample_rate=1, tags=None):
        self.statsd = statsd
        if tags is None:
            tags = []
        self.tags = tags

        self.name = name
        self.sample_rate = sample_rate

    def __enter__(self):
        self.start_time = time.time()
        self.start_cpu_time = get_cpu_time()
        return self

    @property
    def time(self):
        return self.end_time - self.start_time

    @property
    def cpu_time(self):
        return self.end_cpu_time - self.start_cpu_time

    def __exit__(self, exc_type, exc_value, traceback):
        self.end_time = time.time()
        self.end_cpu_time = get_cpu_time()

        self.statsd.timing(self.name,
            self.time,
            sample_rate=self.sample_rate,
            tags=self.tags)
        self.statsd.timing('{}.cpu'.format(self.name),
            self.cpu_time,
            sample_rate=self.sample_rate,
            tags=self.tags)


class StatsdMiddleware(object):
    def __init__(self, app, statsd):
        self.app = app
        self.wsgi_app = app.wsgi_app
        self.statsd = statsd

    def _metric_name_from_path(self, path):
        uuid_regex = '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        path = path.split('?')[0]
        return re.sub(uuid_regex, 'id', path).rstrip('/').lstrip('/').replace('/', '.')

    def __call__(self, environ, start_response):
        def start_response_wrapper(*args, **kwargs):
            status = args[0].split(' ')[0]
            self.status = status
            return start_response(*args, **kwargs)

        metric_name = '{}.{}'.format(
            self.app.name,
            self._metric_name_from_path(environ['PATH_INFO'])
        )
        with TimingStats(self.statsd, metric_name) as metric:
            response = self.wsgi_app(environ, start_response_wrapper)
            metric.tags.append('http_status_code:{}'.format(self.status))
            metric.tags.append('http_method:{}'.format(environ['REQUEST_METHOD']))

        self.statsd.timing('{}.api.request'.format(self.app.name), metric.time, tags=metric.tags)
        self.statsd.timing('{}.api.request.cpu'.format(self.app.name), metric.cpu_time, tags=metric.tags)

        return response
