# Asstools
==========

A few scripts that use [python-ass](https://github.com/knitori/python-ass) or
other tools to manage ASS (Advanced SubStation Alpha) files.

Currently only a merge script

    merge.py [-t title] [-r] [-g milliseconds] ([-s milliseconds] filename)

```-t``` set a title for the merged ASS file.

```-r``` rename all style names, with hashes

```-g``` set a global synchronisation offset (shifts all .ass files by -g millisecndos)

```-s``` set a per-file synchronisation offset (has higher precedence than -g)
