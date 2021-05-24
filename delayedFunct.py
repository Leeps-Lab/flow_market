from .infiniteTimer import InfiniteTimer
from otree.db import idmap

def call_with_delay(delay: float, callback, *args, **kwargs):
    """Calls a model method with a specified delay

    Uses Timer to create a delay, then starts a new database session, rebinds the
    method to a fresh copy of its model and calls it.
    NOTE: This function will only work when `callback` is a method on some model (Group, Player, etc.).
    Don't try calling it with a lambda function or something, it won't work."""
    if delay <= 0:
        callback(*args, **kwargs)
        return

    self = callback.__self__
    cls = type(self)

    def query_and_call():
        with idmap.use_cache():
            new_model = cls.objects.get(id=self.id)
            callback.__func__.__get__(new_model, cls)(*args, **kwargs)

    t = InfiniteTimer(delay, query_and_call)
    t.start()