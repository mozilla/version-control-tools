#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Script to extract data from XML files.

import sys

from lxml import etree

def main(args):
    path, xpath = args[0:2]

    parser = etree.XMLParser(resolve_entities=False)
    tree = etree.parse(path, parser=parser)

    for el in tree.xpath(xpath):
        print(etree.tostring(el, encoding='utf-8', pretty_print=True).strip())

sys.exit(main(sys.argv[1:]))
