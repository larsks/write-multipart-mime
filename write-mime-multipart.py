#!/usr/bin/env python

import os
import sys
import argparse
import mimetypes

from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


starts_with_mappings = {
    '#include': 'text/x-include-url',
    '#!': 'text/x-shellscript',
    '#cloud-config': 'text/cloud-config',
    '#upstart-job': 'text/upstart-job',
    '#part-handler': 'text/part-handler',
    '#cloud-boothook': 'text/cloud-boothook',
}

mimetypes.add_type('text/x-markdown', '.md')

def guess_mimetype(path):
    global args
    with open(path) as fd:
        firstline = fd.readline()
        for value, mimetype in starts_with_mappings.items():
            if firstline.startswith(value):
                return mimetype, None

    mimetype = mimetypes.guess_type(path)
    return mimetype if mimetype else args.default_mimetype


def parse_args():
    p = argparse.ArgumentParser()

    p.add_argument('--output', '-o')
    p.add_argument('--merge', '-M')
    p.add_argument('--default-mimetype', '-T',
                   default='application/octet-stream')

    p.add_argument('part', nargs='+')

    return p.parse_args()


def main():
    global args
    args = parse_args()
    
    container = MIMEMultipart()

    for part in args.part:
        if ':' in part:
            path, mimetype = part.split(':')
            encoding = None
        else:
            path = part
            mimetype, encoding = guess_mimetype(path)

        if mimetype is None:
            print >>sys.stderr, 'ERROR: unable to determine mime type ' \
                'for file $part.'
            sys.exit(1)

        maintype, subtype = mimetype.split('/', 1)
        with open(path) as fd:
            content = fd.read()

        if maintype == 'text':
            data = MIMEText(content, _subtype=subtype)
        elif maintype == 'image':
            data = MIMEImage(content, _subtype=subtype)
        elif maintype == 'audio':
            data = MIMEAudio(content, _subtype=subtype)
        else:
            data = MIMEBase(maintype, subtype)
            data.set_payload(content)
            encoders.encode_base64(data)

        if args.merge:
            data.add_header('X-Merge-Type',
                                 args.merge)

        container.attach(data)

    with open(args.output, 'w') if args.output else sys.stdout as fd:
        fd.write(container.as_string())

if __name__ == '__main__':
    main()

