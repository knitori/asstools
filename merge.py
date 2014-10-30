#!/usr/bin/env python

from functools import reduce
from datetime import timedelta
import sys
import re
import hashlib

import ass

EventTypes = (ass.document.Dialogue, ass.document.Comment)
StyleTypes = (ass.document.Style,)

FIELDS_ONLY = (
    'PlayResX',
    'PlayResY',
    'ScaledBorderAndShadow',
    'ScriptType',
    'Title',
    'WrapStyle',
    'YCbCr Matrix')


def my_repr(self):
    return '<AssDoc events={} styles={} {}>'.format(
        len(self.events),
        len(self.styles),
        hex(id(self)))

ass.document.Document.__repr__ = my_repr


def _camel_case_conv(text):
    """Convert CamelCase to camel_case."""
    def _replace(match):
        return '_' + match.group(1).lower()
    text = text[0:1].lower() + text[1:]
    return re.sub(r'([A-Z])', _replace, text)


def copy_event(event):
    assert isinstance(event, EventTypes)
    if event.TYPE == 'Dialogue':
        newevent = ass.document.Dialogue()
    elif event.TYPE == 'Comment':
        newevent = ass.document.Comment()

    for field, value in event.fields.items():
        field = _camel_case_conv(field)
        field = field.replace('colour', 'color')
        assert getattr(event, field, None) is not None, field
        setattr(newevent, field, value)
    return newevent


def copy_style(style):
    newstyle = ass.document.Style()
    for field, value in style.fields.items():
        field = _camel_case_conv(field)
        field = field.replace('colour', 'color')
        assert getattr(style, field, None) is not None, field
        setattr(newstyle, field, value)
    return newstyle


def copy(doc):
    newdoc = ass.document.Document()
    if doc.fields is not None:
        for key, value in doc.fields.items():
            if key not in FIELDS_ONLY:
                continue
            newdoc.fields[key] = value

    for event in doc.events:
        newdoc.events.append(copy_event(event))

    for style in doc.styles:
        newdoc.styles.append(copy_style(style))

    return newdoc


def shift(doc, by_microseconds, *, start=True, end=True):
    newdoc = copy(doc)
    for event in newdoc.events:
        assert isinstance(event, EventTypes)
        if start:
            event.start += timedelta(microseconds=by_microseconds)
        if end:
            event.end += timedelta(microseconds=by_microseconds)
    return newdoc


def merge(*docs, rename_styles=False):

    newdoc = ass.document.Document()
    # just copy the first doc headers (lazy)
    if docs[0].fields is not None:
        for key, value in docs[0].fields.items():
            if key not in FIELDS_ONLY:
                continue
            newdoc.fields[key] = value

    for index, doc in enumerate(docs):
        if rename_styles:
            rename_mapping = {}

        usedstyles = set()
        for event in doc.events:
            assert isinstance(event, EventTypes)

            newevent = copy_event(event)

            usedstyles.add(newevent.style)  # uses original name
            style_name = newevent.style
            if rename_styles:
                digest = hashlib.sha1()
                digest.update(style_name.encode('utf-8'))
                digest.update('{}'.format(index).encode('ascii'))
                rename_mapping[(index, style_name)] = digest.hexdigest()
                newevent.style = rename_mapping[(index, style_name)]

            if not newevent.text:
                continue

            if style_name not in usedstyles:
                usedstyles.add(style_name)

            newdoc.events.append(newevent)

        for style in doc.styles:
            assert isinstance(style, StyleTypes)

            newstyle = copy_style(style)

            if newstyle.name not in usedstyles:
                continue

            if rename_styles:
                newstyle.name = rename_mapping[(index, newstyle.name)]

            newdoc.styles.append(newstyle)

    return newdoc


def usage(used_command):
    def p(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

    p('Usage: {} [-h|--help] [-r] [-g microseconds] ([-s microseconds] filename)'.format(
        used_command))


def main():
    used_command = sys.argv.pop(0)

    doc_title = None
    rename_styles = False
    global_sync = 0
    files = []

    while sys.argv:
        arg = sys.argv.pop(0)
        if arg in ('-h', '--help'):
            usage(used_command)
            sys.exit(0)
        elif arg == '-r':
            rename_styles = True
        elif arg == '-t':
            doc_title = sys.argv.pop(0)
        elif arg == '-g':
            global_sync = int(sys.argv.pop(0))
        elif arg == '-s':
            file_sync = int(sys.argv.pop(0))
            filename = sys.argv.pop(0)
            files.append((file_sync, filename))
        else:
            files.append((None, arg))

    docs = []
    for sync, filename in files:
        if sync is None:
            sync = global_sync

        print('', file=sys.stderr)
        print('File: {}'.format(filename), file=sys.stderr)
        print('  Sync: {}'.format(sync), file=sys.stderr)
        print('', file=sys.stderr)

        with open(filename, 'r') as f:
            doc = ass.parse(f)

        if sync != 0:
            doc = shift(doc, sync)
        docs.append(doc)

    merged_docs = merge(*docs, rename_styles=rename_styles)
    if doc_title is not None:
        merged_docs.fields['Title'] = doc_title

    merged_docs.dump_file(sys.stdout)


if __name__ == '__main__':
    main()
