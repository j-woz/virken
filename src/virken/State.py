
# STATE PY

from enum import Enum
import datetime, os, stat
import logging
import subprocess


from virken.log_tools import logger_get
import virken.Utils   as     Utils


class State:

    """
    The overall state of Virken.
    Contains the table of VC entries.
    """

    class Diff(Enum):
        """ Type of diff to perform """
        LINE = 1
        WORD = 2

    def __init__(self):
        # The Version Control system object
        # (vc_svn or vc_git or vc_fs)
        self.VC = None
        # If True, we will force a VC.status() call
        self.stale = True
        # The list of all Entries, shown or not
        self.table = None
        # The Display object
        self.display = None
        # Where the pointer is
        # If the State is empty, this is 0
        self.current = 1
        # First entry shown on this page
        self.offset = 1
        self.logger_state = None
        self.logger_cache = None
        self.logger_state = logger_get(self.logger_state, "State")
        self.logger_cache = logger_get(self.logger_cache, "Cache")
        # Whether to ignore according to VC
        self.ignores = True
        # Whether to show file stats (timestamp, size)
        self.stats = False
        # Whether to use worddiff
        self.diff_type = State.Diff.LINE
        # A single string glob pattern
        self.glob_pattern = None
        # A list of patterns to ignore
        # May be None if there are no patterns (or FNF)
        self.fs_ignores = None
        # Did we do a chdir()?
        self.chdir = False
        self.marks_loaded = None
        # Caches of FS information, may go stale
        # Map from filename to os.stat() result object
        #     or None if file-not-found
        self.cache_stats = {}
        self.cache_links = {}

    def load_fs_ignores(self, cfg):
        if os.path.exists(cfg):
            self.fs_ignores = Utils.read_list(cfg)
        else:
            self.fs_ignores = None

    def toggle_ignores(self):
        self.ignores = not self.ignores
        msg = "Ignoring as normal."    \
              if self.ignores          \
              else "Ignores disabled!"
        self.display.warn(msg)
        self.stale = True

    def toggle_stats(self):
        self.stats = not self.stats
        self.stale = True

    def toggle_worddiff(self):
        self.diff_type = State.Diff.WORD \
            if self.diff_type == State.Diff.LINE \
               else State.Diff.LINE
        msg = "diff type: "
        msg += "line" if self.diff_type == State.Diff.LINE \
            else "word"
        self.display.warn(msg, timeout=2)

    def show(self):
        """ Returns a string that will prefix the main menu prompt """
        self.debug("show(): offset=%i" % self.offset)
        if self.stale:
            self.table = self.VC.status(self.ignores)
            self.stale = False
            self.marks_load()
            self.chdir = False
            self.cache_stats.clear()
            self.cache_links.clear()

        self.height, self.width = self.display.window.getmaxyx()
        self.debug("height,width=%i,%i" %
                   (self.height,self.width))
        # table[0] is a sentinel "NULL"
        n = len(self.table)-1

        if len(self.table) > 0:
            if self.current < 1:
                self.current = 1
            if self.current > n:
                self.current = n
        else:
            self.current = 0

        self.info("table total size: %i" % n)
        # Modifiers to prompt:
        modifiers = []
        # Maximal number of entries we can show:
        self.menu_space = self.height - self.display.overhead
        if self.offset > 1:
            modifiers.append("PREV")
        if n > self.offset + self.menu_space:
            modifiers.append("NEXT")

        # Number of entries actually shown
        self.shown = min(self.menu_space, n-(self.offset-1))
        self.info("shown=%i" % self.shown)

        self.display.window.clear()
        info_line = self.VC.info
        if self.glob_pattern is not None:
            info_line += (" (%s)" % self.glob_pattern)
        self.display.title(info_line)

        if len(self.table) == 1:
            self.display.at(6, 6, "( NOTHING TO SHOW ) ")
            return "NOTHING"

        entries = []
        for index in range(self.offset, self.offset+self.shown):
            entries.append((index, self.table[index]))
        self.show_entries(entries)
        result = self.format_prompt_modifiers(modifiers)
        return result

    def get_mark(self, name):
        result = " "  # default
        if self.table is not None:
            for entry in self.table:
                if "NULL" == entry: continue
                if entry.name == name:
                    result = entry.mark
        return result

    def show_entries(self, entries):
        max_length = 0
        for index, entry in entries:
            if len(entry.name) > max_length:
                max_length = len(entry.name)
        index = 0
        # self.display.warn("max_length: %i" % max_length)
        # TODO: Calc max line length so we can shrink file
        #       names if needed
        #       The stat field is now 26 characters
        _, width = self.display.window.getmaxyx()
        fmt = "%3s %2i) %-" + str(max_length+4) + "s"
        # menu_pointer is 5+1
        # mark is 3
        name_max = width - (5+1+3+1+2+2+2)
        if self.stats:
            fmt += " %-26s"
            name_max -= 27
        else:
            fmt += "%s"
        # self.logger_state.debug("entry fmt='%s'" % fmt)
        # self.logger_state.debug("name_max=%i" % name_max)
        for index, entry in entries:
            self.show_entry(index, entry, fmt, name_max)

    def show_entry(self, index, entry, fmt, name_max):
        filename = self.table[index].name
        s = self.lookup_stats(filename) if self.stats else ""
        stats = State.show_stat(s)
        self.display.menu_pointer(self.offset, index, index==self.current)
        line = fmt % (entry.mark, index, entry.show(name_max), stats)
        self.display.menu_content(self.offset, index, line)

    def format_prompt_modifiers(self, modifiers):
        if len(modifiers) == 0:
            return ""
        counts = "%i/%i" % (self.offset, len(self.table)-1)
        return "(%s %s)" % (",".join(modifiers), counts)

    def get_selected_filenames(self, mark=">", none_ok=False):
        """ none_ok : if True, nothing selected means return nothing,
                      not current
            @return: List of string filenames
        """
        entries = self.get_selected_entries(mark=mark,
                                            none_ok=none_ok)
        result = []
        for entry in entries:
            result += entry.names()
        self.info("get_selected_filenames: '%s' %s" %
                         (mark, str(result)))
        return result

    def get_selected_entries(self, mark=">", none_ok=False):
        """ none_ok : if True, nothing selected means return nothing,
                      not current
            @return: List of Entry objects
        """
        selected = self.get_entries(mark)
        if len(selected) > 0:
            return selected
        if self.current == 0:
            return []
        if none_ok:
            return []
        return [ self.table[self.current] ]

    def get_entries(self, c):
        """ Return list of Entry objects marked with c """
        result = []
        for entry in self.table:
            if "NULL" == entry: continue
            if entry.mark == c:
                result.append(entry)
        self.logger_state.info("get_entries(): " + str(result))
        return result

    def key_up(self):
        self.display.menu_pointer(self.offset, self.current, False)
        self.current = self.current - 1
        if self.current < self.offset:
            self.current = self.offset
        self.display.menu_pointer(self.offset, self.current, True)

    def key_down(self):
        self.display.menu_pointer(self.offset, self.current, False)
        self.current = self.current + 1
        if self.current >= self.offset + self.shown - 1:
            self.current = self.offset + self.shown - 1
        self.display.menu_pointer(self.offset, self.current, True)

    def page_up(self):
        height, width = self.display.window.getmaxyx()
        self.offset = self.offset - (height-self.display.overhead)
        if self.offset < 1: self.offset = 1
        self.current = self.offset

    def page_down(self):
        n = len(self.table) - 1
        if self.offset == n:
            self.display.warn("No more entries!")
        self.offset = self.offset + self.menu_space
        if self.offset > n:
            self.offset = n
        self.current = self.offset

    def select(self):
        if self.current == 0:
            return
        entry = self.table[self.current]
        entry.mark = ">" if entry.mark == " " else " "
        if entry.mark == ">":
            self.key_down()

    def select_all(self):
        for i in range(1, len(self.table)):
            self.table[i].mark = ">"

    def select_zero(self):
        for i in range(1, len(self.table)):
            self.table[i].mark = " "

    def edit(self):
        filenames = self.get_selected_filenames()
        # errs = None
        Utils.editor_files(self.display, filenames)
        # if errs != None:
        #     sys.stderr.write(errs)
        #     Utils.pager_str(self.display, errs)

    def examine(self):
        filenames = self.get_selected_filenames()
        # errs = None
        rc = Utils.pager_files(self.display, filenames)
        if not rc:
            # sys.stderr.write(errs)
            # Utils.pager_str(self.display, ")
            self.display.warn("pager failed!")

    def glob_ask(self):
        g = self.display.ask("glob: ")
        g = g.strip()
        if g == "":
            self.glob_pattern = None
        else:
            self.glob_pattern = g
        self.stale = True

    # REO = Regular Expression Object
    def glob_compile(self):
        if self.glob_pattern is None:
            return None
        import re
        try:
            reo = re.compile(self.glob_pattern)
        except re.error as e:
            self.glob_error(e)
            reo = None
        return reo

    def glob_error(self, e):
        text = str(e)  # exception text
        msg = "bad glob: '%s': %s" % (self.glob_pattern, text)
        self.logger_state.warn("glob_compile(): exception: %s" %
                         str(type(e)))
        self.logger_state.warn("glob_compile(): " + msg)
        self.display.warn(msg, timeout=10)

    def glob_match(self, reo, name):
        if reo is None: return True
        match = reo.search(name)
        return match is not None

    def jump_ask(self):
        n = self.display.ask("jump: ")
        n = n.strip()
        if n == "":
            return
        if not Utils.is_int(n):
            self.display.warn("jump: invalid: '%s' " % n)
            return
        self.current = int(n)

    def revert(self):
        filenames = self.get_selected_filenames()
        for filename in filenames:
            self.VC.revert(filename)

    def mark_delete(self):
        self.mark("X")

    def mark_backup_mv(self):
        self.mark("k")

    def mark_backup_cp(self):
        self.mark("K")

    def mark(self, c):
        entries = self.get_selected_entries()
        for entry in entries:
            if "NULL" == entry: continue
            entry.mark = c if entry.mark != c else " "

    def marks_save(self):
        D = {}
        for entry in self.table:
            if entry      == "NULL": continue
            if entry.mark == " ":    continue
            D[entry.name] = entry.mark
        marks_json = ".virken.json"
        if not any(D):
            if os.path.exists(marks_json):
                self.display.warn("Save: No marks: deleting file...")
                os.remove(marks_json)
            else:
                self.display.warn("Save: No marks: nothing to do.")
        else:
            import json
            with open(marks_json, "w") as fp:
                json.dump(D, fp)
            self.display.warn("Saved marks.")

    def marks_load(self, force=False):
        """ force: If True, load marks even if nothing changed """
        if not self.marks_load_from_file(force):
            return
        for entry in self.table:
            if entry == "NULL": continue
            if entry.name in self.marks_loaded:
                entry.mark = self.marks_loaded[entry.name]

    def marks_load_from_file(self, force):
        """ force: If True, load marks even if nothing changed """
        marks_json = ".virken.json"
        # self.display.warn("load: chdir: " + str(self.chdir))
        if not force:
            if not self.chdir and self.marks_loaded is not None:
                # Nothing changed- use current state
                return False
            if not os.path.exists(marks_json):
                # Store empty dict to remember we looked for JSON:
                self.marks_loaded = {}
                return False
        try:
            with open(marks_json, "r") as fp:
                import json
                self.marks_loaded = json.load(fp)
        except Exception as e:
            msg = "could not open: %s : %s" % (marks_json, str(e))
            self.logger_state.warning("marks_load_from_file(): " + msg)
            self.display.warn(msg, timeout=10)
            return False
        self.info("Loaded marks.")
        self.display.warn("Loaded marks.")
        return True

    def expunge(self):
        self.expunge_deleted()
        self.expunge_backup_cp()
        self.expunge_backup_mv()
        self.stale = True

    def expunge_deleted(self):
        filenames = self.get_selected_filenames("X", none_ok=True)
        count = len(filenames)
        if count == 0:
            return
        c = self.display.ask1("Delete: %i file%s? (y/n)" %
                              (count, Utils.plural(count)))
        if c != "y": return
        for filename in filenames:
            try:
                os.remove(filename)
            except Exception as e:
                self.display.warn("Could not delete: '%s' : %s" %
                                  (filename, str(e)))

    def expunge_backup_cp(self):
        filenames = self.get_selected_filenames("K", none_ok=True)
        count = len(filenames)
        if count == 0:
            return
        c = self.display.ask1("Backup copy: %i file%s? (y/n)" %
                              (count, Utils.plural(count)))
        if c != "y": return
        for filename in filenames:
            Utils.make_backup_cp(filename)

    def expunge_backup_mv(self):
        filenames = self.get_selected_filenames("k", none_ok=True)
        count = len(filenames)
        if count == 0:
            return
        c = self.display.ask1("Backup move: %i file%s? (y/n)" %
                              (count, Utils.plural(count)))
        if c != "y": return
        for filename in filenames:
            Utils.make_backup_mv(filename)

    def cd(self):
        self.logger_state.info("cd(): self.current=%i" % self.current)
        if self.current == 0:
            self.display.warn("Nothing to do!")
            return
        entry = self.table[self.current]
        if not os.path.isdir(entry.name):
            self.display.warn("Not a directory!")
            return
        os.chdir(entry.name)
        self.stale = True
        self.logger_state.info("cd(): dir: '%s'" % entry.name)
        self.chdir = True

    def cd_up(self):
        os.chdir("..")
        self.stale = True
        self.chdir = True

    def stash_push(self):
        global logger_state
        filenames = self.get_selected_filenames(none_ok=False)
        if len(filenames) == 0:
            self.display.warn("No files!")
            return
        command = [ "stash", "push" ]
        command += filenames
        self.logger_state.info("command: " + str(command))
        subprocess.run(command)

    def stash_pop(self):
        global logger_state
        filenames = self.get_selected_filenames(none_ok=False)
        if len(filenames) == 0:
            self.display.warn("No files!")
            return
        command = [ "stash", "pop" ]
        filenames = self.stash_drop_suffixes(filenames)
        command += filenames
        self.logger_state.info("command: " + str(command))
        subprocess.run(command)

    def stash_drop_suffixes(self, filenames):
        """ Each of these filenames ends in .stash - cut that """
        results = []
        for f in filenames:
            results.append(f[0:-6])  # len(".stash") == 6
        return results

    def search(self):
        pattern = self.display.ask("search: ")
        if len(pattern.strip()) == 0:
            return
        index = self.current + 1
        while True:
            if index >= len(self.table):
                self.display.warn("search: not found!")
                break
            entry = self.table[index]
            if pattern in entry.name:
                self.current = index
                break
            index += 1

    def lookup_stats(self, filename):
        # self.logger_cache = logger_get(self.logger_cache, "Cache")
        self.logger_cache.setLevel(logging.DEBUG)
        if filename not in self.cache_stats:
            self.logger_cache.info("MISS: " + filename)
            result = self.do_stat(filename)
        else:  # Found in cache
            self.logger_cache.info("HIT:  " + filename)
            result = self.cache_stats[filename]
        return result

    def do_stat(self, filename):
        try:
            s = os.stat(filename)
        except FileNotFoundError:
            # self.logger_cache = logger_get(self.logger_cache, "Cache")
            try:
                s = os.lstat(filename)
            except FileNotFoundError:
                self.logger_cache.info("FNF:  " + filename)
                s = "FNF"
            else:
                self.logger_cache.info("LNK!:  " + filename)
                s = "BROKEN_LINK"
        self.cache_stats[filename] = s
        return s

    def show_stat(s):
        if type(s) == str: return s
        sz = s.st_size
        mt = s.st_mtime
        dt = datetime.datetime.fromtimestamp(mt)
        ds = dt.strftime("%Y-%m-%d %H:%M")
        return Utils.bytes_human(sz) + " " + ds

    def is_executable(self, filename) -> bool:
        s = self.lookup_stats(filename)
        assert s is not None, "could not do stat: " + filename
        if s == "BROKEN_LINK":
            return False
        result = bool(s.st_mode & stat.S_IEXEC) and \
                 not stat.S_ISDIR(s.st_mode)
        if result: self.logger_state.info("executable: " + filename)
        return result

    def is_directory(self, filename):
        s = self.lookup_stats(filename)
        result = stat.S_ISDIR(s.st_mode)
        if result: self.logger_state.info("directory: " + filename)
        return result

    def is_link(self, filename):
        if filename in self.cache_links:
            result = self.cache_links[filename]
        else:
            result = os.path.islink(filename)
            self.cache_links[filename] = result
        return result

    def is_broken_link(self, filename):
        # https://stackoverflow.com/questions/20794/find-broken-symlinks-with-python
        return self.is_link(filename) and not os.path.exists(filename)

    def info(self, msg):
        self.logger_state.info(msg)

    def debug(self, msg):
        self.logger_state.debug(msg)
