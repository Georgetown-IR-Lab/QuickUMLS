try:
    from quickumls import QuickUMLS
    from network import run_server
except ImportError:
    from .quickumls import QuickUMLS
    from .MinimalServer import run_server

from argparse import ArgumentParser


def run_quickumls_server(opts):
    matcher = QuickUMLS(
        quickumls_fp=opts.quickumls_fp,
        threshold=opts.threshold,
        overlapping_criteria=opts.overlapping_criteria,
        similarity_name=opts.similarity_name,
        window=opts.window,
        min_match_length=opts.min_match_length,
        verbose=opts.verbose
    )

    run_server(matcher, host=opts.host, port=opts.port, buffersize=4096)


if __name__ == '__main__':
    ap = ArgumentParser(
        prog='QuickUMLS server',
        description=(
            'For more detailed instructions, visit '
            'github.com/Georgetown-IR-Lab/QuickUMLS'
        )
    )

    # required arguments
    ap.add_argument(
        'quickumls_fp',
        help='directory where the QuickUMLS data files are installed.'
    )

    # server configuration
    ap.add_argument(
        '-H', '--host', default='localhost',
        help='host of the server'
    )
    ap.add_argument(
        '-P', '--port', default=4645, type=int,
        help='port on which the script responds'
    )

    # QuickUMLS options
    ap.add_argument(
        '-t', '--threshold', default=0.7, type=float,
        help='minimum similarity value between strings'
    )
    ap.add_argument(
        '-o', '--overlapping_criteria', default='score',
        choices=['score', 'length'],
        help='criteria used to deal with overlapping concepts'
    )

    ap.add_argument(
        '-s', '--similarity_name', default='jaccard',
        choices=['dice', 'jaccard', 'cosine', 'overlap'],
        help='name of similarity to use'
    )
    ap.add_argument(
        '-w', '--window', default=5, type=int,
        help='maximum number of tokens to consider for matching'
    )
    ap.add_argument(
        '-l', '--min-match-length', default=3, type=int,
        help='minimum length of a match'
    )
    ap.add_argument(
        '-v', '--verbose', action='store_true',
        help='return verbose information while running'
    )

    opts = ap.parse_args()
    run_quickumls_server(opts)
