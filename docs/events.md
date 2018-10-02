Events
======

An extensible event framework is built-in.

Things to keep in mind:
- The order of event handler calls is not guaranteed.
- Event handlers cannot return anything. However, they can modify the arguments they receive.


Register for an event
---------------------

To register for an event, get the context, `cli_ctx`, and call `register_event()`.

When an event is raised, the first argument is the context, `cli_ctx` and `kwargs` is any keyword arguments passed in by the raiser of the event (so this is event specific).

```Python
def event_handler(cli_ctx, **kwargs):
    print(kwargs)

self.cli_ctx.register_event(EVENT_NAME, event_handler)
```

Raise your own events
---------------------

The framework has some events built-in.
For the full list of events, see [events](../knack/events.py).

You can also add your own events.

```Python
self.cli_ctx.raise_event(EVENT_NAME, arg1=arg1, arg2=arg2, ...)
```
