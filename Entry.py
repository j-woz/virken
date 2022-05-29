
# ENTRY
# Entries in the Status table

from log_tools import logger_get


class Entry:

    ''' Most entries A, M, etc. '''

    def __init__(self, mark, state, name, name_display):
        self.mark  = mark
        self.state = state
        self.name  = name
        self.name_display = name_display

    def __str__(self):
        return "Entry: %s %s %s" % (self.mark, self.state, self.name)

    def show(self, name_max):
        return self.state + " " + self.shrink_name(name_max)

    def shrink_name(self, name_max):
        if len(self.name_display) > name_max:
            return self.name_display[0:name_max]
        return self.name_display

    def get_stats(self):
        import datetime, os
        import Utils
        try:
            s = os.stat(self.name)
        except FileNotFoundError:
            return "File Not Found"
        self.state.cache[self.name] = s
        sz = s.st_size
        mt = s.st_mtime
        dt = datetime.datetime.fromtimestamp(mt)
        ds = dt.strftime("%Y-%m-%d %H:%M")
        return Utils.bytes_human(sz) + " " + ds


class EntryRename(Entry):

    ''' File renaming entries R -> '''

    def __init__(self, mark, state, fromfile, name):
        self.mark     = mark
        self.state    = state
        self.fromfile = fromfile
        self.name     = name

    def __str__(self):
        return "Entry: %s %s %s -> %s" % \
            (self.mark, self.state, self.fromfile, self.name)

    def show(self):
        return self.state + " " + self.fromfile + " -> " + self.name
