# plugins/referrer_policy.py

from datasette import hookimpl

@hookimpl
def asgi_wrapper(datasette):
    def wrap(app):
        async def send_with_header(scope, receive, send):
            async def send_modified(event):
                if event["type"] == "http.response.start":
                    headers = dict(event.get("headers", []))
                    # Add or overwrite the Referrer-Policy header
                    headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                    event["headers"] = list(headers.items())
                await send(event)
            await app(scope, receive, send_modified)
        return send_with_header
    return wrap