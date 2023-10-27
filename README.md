
= Virken

A Version Control Menu tool.

Simply wraps the output of +git status+ in a useful menu, so you can quickly view, edit, diff, revert, and commit changes, etc., often with single keystrokes.

== Meaning

The name is just a play on version control, but coincidentally means "work" in Danish.

== Dependencies

Requires Python 3.6 for PosixPath iterable stuff.  No other packages.

Implemented Python's +curses+ library and typical command-line tools.

== Known issues

Currently cannot run +vi+ as editor due to unknown incompatibility.
Works fine with +nano+, +emacs+, +ed+.
