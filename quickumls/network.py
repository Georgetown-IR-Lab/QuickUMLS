"""Minimal client server through sockets
https://github.com/lucasoldaini/MinimalServer"""

import datetime
import inspect
import math
import socket
import sys
import threading
import time

import six

try:
    import cPickle as pickle
    import SocketServer as socketserver
except ImportError:
    import pickle
    import socketserver


def pad_message(message, blocklength):
    """Pad a message so its length is a multiple of blocklength."""
    message_padded_length = int(math.ceil(len(message) / blocklength)) * blocklength
    padded_message = message.ljust(message_padded_length)
    return padded_message


def receive_data_in_chunks(sock, buffersize):
    """Receive data in chunks of size buffersize from the socket"""
    chunk = sock.recv(buffersize)
    chunks = [chunk]

    # keep reading until chunks are available
    while len(chunk.strip()):
        chunk = sock.recv(buffersize)
        chunks.append(chunk)

    data = b"".join(chunks).strip()
    return data


def send_data_in_chunks(data, sock, buffersize):
    """Split the message into chunks ans send it"""
    sock.sendall(pad_message(data, buffersize))

    # We sent an empty chunk to signal that we're done
    # transmitting the message.
    sock.send(b" " * buffersize)


class MinimalServerHandler(socketserver.BaseRequestHandler):
    """Handle requests to the TCP server"""

    def handle(self):
        """Handle request by executing the specified method from the
        served object"""

        # receives data
        data = receive_data_in_chunks(self.request, self.server.buffersize)

        # parses the target method name, args, and kwargs
        method_name, args, kwargs = pickle.loads(data)

        # try executing the method from the server object, if it
        # fails, pass the error as response (the client will raise
        # the expection)
        try:
            response = getattr(self.server.served_object, method_name)(*args, **kwargs)
        except Exception as ex:
            response = ex

        # send the response to the client in chunks
        send_data_in_chunks(
            pickle.dumps(response, protocol=self.server.pickle_protocol),
            self.request,
            self.server.buffersize,
        )


class MinimalServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCP Server"""

    served_object = None
    buffersize = 2048
    pickle_protocol = None


class MinimalClient(object):
    """Minimal client to provide communication with the server"""

    def __init__(
        self,
        target_class,
        host="localhost",
        port=4444,
        buffersize=2048,
        pickle_protocol=None,
    ):
        """Initialize the client
        Args:
            target_class (object): the class to be served by the
                server. Only public methods will be binded.
            host (str or unicode): the host address of the server.
            port (int): the port the server is listening to.
            buffersize (int): the size of the buffer used for communication.
                Must be the same for both the server and the client.
            pickle_prtocol (int or None): the version number of the protocol
                used to pickle / unpickle objects. Necessary to be set
                if and only if server and client are running on different
                Python versions.
        """

        if pickle_protocol is None:
            pickle_protocol = pickle.HIGHEST_PROTOCOL

        self.host = host
        self.port = port
        self.buffersize = buffersize
        self.pickle_protocol = pickle_protocol

        if six.PY2:
            predicate = inspect.ismethod
        else:
            predicate = inspect.isfunction

        # bind public methods on target_class here
        for method_name, method in inspect.getmembers(
            target_class, predicate=predicate
        ):
            if method_name.startswith("_"):
                continue
            setattr(self, method_name, self._func_req_wrapper(method_name))

    def _func_req_wrapper(self, method_name):
        """create a method with the same method_name that communicate
        with the server"""

        def func_request(*args, **kwargs):
            """Send the request to the server"""

            # prepare the data
            data = pickle.dumps(
                (method_name, args, kwargs), protocol=self.pickle_protocol
            )

            # open the socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))

            # tries sending the data and getting a response back
            try:
                send_data_in_chunks(data, sock, self.buffersize)
                response = receive_data_in_chunks(sock, self.buffersize)
            finally:
                sock.close()

            try:
                # unpickles the response
                data = pickle.loads(response)
            except EOFError:
                # server sent an empty message"
                msg = "empty message received from the server."
                raise RuntimeError(msg)

            # raises an exception if an exception was raised by the
            # served object while the server was executing method named
            # method_name
            if isinstance(data, Exception):
                raise data

            return data

        return func_request


def run_server(
    served_object, host="localhost", port=4444, buffersize=2048, pickle_protocol=None
):
    """Runs the server
    Args:
        served_obkect (object): the object to be served by the
            server. Only public methods will be served.
        host (str or unicode): the host address of the server.
        port (int): the port the server is listening to.
        buffersize (int): the size of the buffer used for communication.
            Must be the same for both the server and the client.
        pickle_prtocol (int or None): the version number of the protocol
            used to pickle / unpickle objects. Necessary to be set
            if and only if server and client are running on different
            Python versions.
    """

    if pickle_protocol is None:
        pickle_protocol = pickle.HIGHEST_PROTOCOL

    # allows port reuse
    MinimalServer.allow_reuse_address = True

    # Initialize the server, set served_object, buffersize, pickle_prtocol
    server = MinimalServer((host, port), MinimalServerHandler)
    server.served_object = served_object
    server.buffersize = buffersize
    server.pickle_protocol = pickle_protocol

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print(
        "[{}] server running at {}:{} (press ^C to interrupt)".format(
            datetime.datetime.now().isoformat(), host, port, server_thread.name
        )
    )

    # Wait for termination
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[{}] server stopped".format(datetime.datetime.now().isoformat()))

    # Terminate the server
    server.shutdown()
    server.server_close()
