"""
Enable SSL transport security for bottle.
"""

from wsgiref import simple_server

import ssl
import bottle


class FixedHandler(simple_server.WSGIRequestHandler):
    """
    Simple handler.
    """

    def address_string(self):
        """
        Prevent reverse DNS lookups.
        """
        return self.client_address[0]


class SecureServerAdapter(bottle.ServerAdapter):
    """
    Wraps SSL around the socket connection.
    """
    def __init__(self, key_file, cert_file,
                 host='0.0.0.0', port=443, **options):
        super().__init__(host, port, **options)
        self.key = key_file
        self.cert = cert_file

    def run(self, handler):
        """
        Run the WSGI server.
        """
        handler_cls = self.options.get('handler_class', FixedHandler)
        server_cls = self.options.get('server_class', simple_server.WSGIServer)

        srv = simple_server.make_server(self.host,
                                        self.port,
                                        handler,
                                        server_cls,
                                        handler_cls)
        srv.socket = ssl.wrap_socket(srv.socket,
                                     keyfile=self.key,
                                     certfile=self.cert,
                                     server_side=True)
        srv.serve_forever()


def get_app(app):
    """
    Wrap HTTP app into HTTPS.
    """
    def https_app(environ, start_response):
        """
        HTTPS app.
        """
        environ['wsgi.url_scheme'] = 'https'
        return app(environ, start_response)

    return https_app
