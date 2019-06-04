from .network import MinimalClient
from .core import QuickUMLS


def get_quickumls_client(host='localhost', port=4645):
    '''Return a client for a QuickUMLS server running on host at port'''
    client = MinimalClient(QuickUMLS, host=host, port=port, buffersize=4096)
    return client
