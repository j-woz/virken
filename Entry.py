
# ENTRY
# Entries in the Status table

from log_tools import logger_get


class Entry:

    ''' Most entries A, M, etc. '''

    def __init__(self, mark, state, name, flags=""):
        self.mark  = mark   # E.g. ">", "X", etc.
        self.state = state  # E.g. "A", "M", etc.
        self.name  = name   # E.g. the file name
        self.flags = flags  # E.g. "*" (executable), "/" (directory)

    def __str__(self):
        result = "Entry: %s %s %s" % (self.mark, self.state, self.name)
        if len(self.flags) > 0: result += "[%s]" % self.flags
        return result

    def show(self, name_max):
        f = len(self.flags)
        if f > 0: name_max = name_max - f
        result = self.state + " " + self.shrink_name(name_max)
        if f > 0: result += "%s" % self.flags
        return result

    def shrink_name(self, name_max):
        if len(self.name) > name_max:
            return self.name[0:name_max]
        return self.name

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
