
# VC GIT

import os
import subprocess

from   virken.vc_base   import vc_base, StatusType
from   virken.State     import State
from   virken.Entry     import Entry, EntryRename
import virken.Utils     as     Utils
import virken.log_tools as     log_tools

logger = None


class vc_git(vc_base):

    def __init__(self, root, state, logger):
        self.name = "GIT"
        super().__init__(root, state, logger)
        self.info = None
        # self.display is assigned by virken.py

    def get_info(self):
        from pathlib import Path
        import configparser

        if self.info is not None:
            return
        config = configparser.ConfigParser()
        config.read(self.root/".git/config")
        if "remote \"origin\"" in config:
            origin = config["remote \"origin\""]

            self.logger.info(str(origin))
            self.logger.info(str(config.sections()))
            self.logger.info(str(config.options("remote \"origin\"")))
            repo = origin["url"]
        else:
            repo = "local repo"
        relative_url = Path(os.getcwd()).relative_to(self.root)

        branch = self.get_branch()

        if repo is None:
            print("Could not find GIT info!")
            exit(1)
        self.info = repo + " " + str(relative_url) + " @" + branch

    def get_branch(self):
        """
        Find the current branch: look for the token after the star
        """
        import subprocess
        command = [ "git", "branch", "--column" ]
        output = subprocess.check_output(command,
                                         stderr=subprocess.STDOUT)
        output = output.decode("utf-8")
        # split output into tokens
        #       on lines, spaces, and flatten resulting list:
        tokens = output.split("\n")
        tokens = list(map(lambda t: t.split(" "), tokens))
        import itertools
        tokens = itertools.chain.from_iterable(tokens)  # flatten
        star = False
        result = "_virken_branch_error"
        for token in tokens:
            token = token.strip(" \n")
            if star:
                result = token
                break
            if token == "*":
                star = True
        return result

    def status(self, ignores):
        global status

        command = [ "git", "status", "--short" ]
        if not ignores:
            command += [ "--ignored" ]
        command += [ "." ]
        p = subprocess.Popen(command, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
        result = self.parse_status(p)
        # p.close() ?
        self.state.table = result
        self.state.stale = False
        return result

    def parse_status(self, p):
        """ p: A subprocess.Popen """
        # reo = Regular Expression Object
        reo = self.state.glob_compile()
        result = [ "NULL" ]
        while True:
            status_type = StatusType.NORMAL
            line = p.stdout.readline().decode("UTF-8")
            if len(line) == 0: break
            line = line.rstrip()

            state = line[0:2]
            state = state.replace(" ", "_")
            if "->" not in line:
                name  = line[3:]
                # Git uses double-quotes on filenames with spaces
                name  = name.replace('"', '')
            else:
                arrow    = line.find("->")
                fromfile = line[2:arrow-1]
                name     = line[arrow+3:]
                fromfile = name.replace('"', '')
                name     = name.replace('"', '')
                status_type = StatusType.RENAME

            if "D" in state:
                status_type = StatusType.DELETED
            if self.state.glob_match(reo, name):
                mark = self.state.get_mark(name)
                flags = ""
                if status_type == StatusType.DELETED:
                    flags += "(X)"
                elif self.state.is_executable(name):
                    flags += "*"
                if self.state.is_broken_link(name):
                    flags += "!"
                if status_type == StatusType.NORMAL or \
                   status_type == StatusType.DELETED:
                    entry = Entry(mark, state, name, flags)
                elif status_type == StatusType.RENAME:
                    entry = EntryRename(mark, state, fromfile, name)
                else:
                    assert(False)
                result.append(entry)
        return result

    def add(self):
        filenames = self.state.get_selected_filenames()
        # self.display.outln("")
        # self.display.warn("git add " + str(filenames))
        command = [ "git", "add" ]
        command += filenames
        Utils.run_simple(self.display, command)

    def diff(self):
        filenames = self.state.get_selected_filenames(none_ok=True)
        # self.display.warn("git diff " + str(filenames))
        command = [ "git", "diff" ]
        if self.state.diff_type == State.Diff.WORD:
            command.append("--word-diff=color")
        command += filenames
        self.logger.info(command)
        # subprocess.run(command) # instant return
        # Utils.run_simple(self.display, command)
        Utils.run_stdout(self.display, command)

    def commit(self):
        filenames = self.state.get_selected_filenames(none_ok=True)
        # self.display.warn("git commit " + str(filenames))
        command = [ "git", "commit" ]
        command += filenames
        Utils.run_simple(self.display, command)

    def revert(self, filename):
        self.logger.info("revert: " + filename)
        Utils.make_backup_cp(filename)
        command = [ "git", "checkout", filename ]
        subprocess.call(command)

    def add_p(self):
        filenames = self.state.get_selected_filenames()
        command = [ "git", "add", "-p" ]
        if len(filenames) == 0:
            filenames = [ "." ]
        command += filenames
        Utils.run_interactive_errors(command)

    def checkout_p(self):
        filenames = self.state.get_selected_filenames()
        command = [ "git", "checkout", "-p" ]
        if len(filenames) == 0:
            filenames = [ "." ]
        command += filenames
        self.logger.info("checkout -p: " + " ".join(filenames))
        for filename in filenames:
            Utils.make_backup_cp(filename)
        Utils.run_interactive_errors(command)

    def diff_cached(self):
        filenames = self.state.get_selected_filenames(none_ok=True)
        command = [ "git", "diff", "--cached", "--color=always" ]
        if len(filenames) == 0:
            filenames = [ "." ]
        command += filenames
        self.logger.info("diff --cached: " + " ".join(filenames))
        Utils.run_stdout(self.display, command)

    def log(self):
        filenames = self.state.get_selected_filenames(none_ok=True)
        command = [ "git", "log" ]
        command += filenames
        self.logger.info(command)
        Utils.run_stdout(self.state.display, command)

    def blame(self):
        filenames = self.state.get_selected_filenames(none_ok=False)
        if len(filenames) != 1:
            self.state.display.warn("Blame requires 1 file!")
            return
        command = [ "git", "blame" ]
        command += filenames
        self.logger.info(command)
        Utils.run_stdout(self.state.display, command)

    def reset_head(self):
        filenames = self.state.get_selected_filenames(none_ok=True)
        for filename in filenames:
            self.logger.info("reset head: " + filename)
            Utils.make_backup_cp(filename)
        command = [ "git", "reset", "HEAD" ]
        command += filenames
        self.logger.info(command)
        subprocess.call(command)

    def reset_patch(self):
        filenames = self.state.get_selected_filenames(none_ok=True)
        for filename in filenames:
            self.logger.info("reset patch: " + filename)
            Utils.make_backup_cp(filename)
        command = [ "git", "reset", "--patch" ]
        command += filenames
        self.logger.info(command)
        Utils.run_interactive_errors(command)
