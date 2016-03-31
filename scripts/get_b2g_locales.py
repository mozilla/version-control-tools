#!/usr/bin/env python

"""
    Get list of locales from file in hg.

    Note: this only works with 'raw-file' urls
"""

import argparse
import logging
import requests
import time

logger = logging.getLogger(__name__)


def get_locales(url):
    return requests.get(url).json()


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help='positional arg', nargs='+')
    parser.add_argument("--bash", default=None, metavar="VERSION",
                        help="Create script for VERSION (e.g. 'v2_5')")
    return parser.parse_args()


def main():
    args = parse_args()
    all_locales = set()
    for u in args.url:
        locales = get_locales(u)
        all_locales.update(locales.keys())
    if args.bash:
        print("# locales taken at %s from:\n"
              "# %s" % (time.asctime(), ' '.join(args.url)))
        template = "locales=(\n  %s\n)"
    else:
        template = "%s"
    print(template % ' '.join(sorted(all_locales)))
    if args.bash:
        print('''/repo/hg/scripts/clone-gaia-l10n.sh -v %s "${locales[@]}"''' %
              args.bash)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    try:
        main()
        raise SystemExit(0)
    except Exception, e:
        raise SystemExit(e)
