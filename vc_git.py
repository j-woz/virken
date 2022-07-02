
# VC GIT

import os
import subprocess

from vc_base import vc_base

from Entry import Entry, EntryRename
from State import State
import Utils

import log_tools

logger = None

class vc_git(vc_base):

    def __init__(self, root, state, logger):
        self.name = "GIT"
        super().__init__(root, state, logger)
        self.info = None
        # self.display is assigned by vcmenu.py

    def get_info(self):
        from pathlib import Path
        import configparser

        if self.info != None:
            return
        url = None
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

        if repo == None:
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
        tokens = itertools.chain.from_iterable(tokens) # flatten
        star = False
        result = "_vcmenu_branch_error"
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
        ''' p: A subprocess.Popen '''
        reo = self.state.glob_compile() # reo = Regular Expression Object
        result = [ "NULL" ]
        while True:
            status_type = "normal"
            line = p.stdout.readline().decode("UTF-8")
            if len(line) == 0:
                break
            line = line.rstrip()
            tokens = line.split(" ")
            if len(tokens) == 2:
                state = tokens[0]
                name  = tokens[1]
            elif len(tokens) == 3:
                if tokens[0] == "":
                    state = "_" + tokens[1]
                elif tokens[1] == "":
                    state = tokens[0] + "_"
                else:
                    self.display.warn("weird line: " + str(tokens))
                    continue
                name = tokens[2]
            # skipping len(tokens) == 4
            elif len(tokens) == 5 and tokens[3] == "->":
                state    = tokens[0] + "_"
                fromfile = tokens[2]
                name     = tokens[4]
                status_type = "rename"
            else:
                self.display.warn("unknown line: " + str(tokens), timeout=10)
                continue
            if self.state.glob_match(reo, name):
                mark = self.state.get_mark(name)
                flags = ""
                if self.state.is_executable(name):
                    flags += "*"
                if self.state.is_broken_link(name):
                    flags += "!"
                if status_type == "normal":
                    entry = Entry(mark, state, name, flags)
                elif status_type == "rename":
                    entry = EntryRename(mark, state, fromfile, name)
                else:
                    assert(False)
                result.append(entry)
        return result

    def add(self):
        filenames = self.state.get_target_filenames()
        # self.display.outln("")
        # self.display.warn("git add " + str(filenames))
        command = [ "git", "add" ]
        command += filenames
        Utils.run_simple(self.display, command)

    def diff(self):
        filenames = self.state.get_target_filenames(none_ok=True)
        # self.display.warn("git diff " + str(filenames))
        command = [ "git", "diff" ]
        if self.state.diff_type == State.Diff.WORD:
            command.append("--word-diff=color")
        command += filenames
        global logger
        self.logger.info(command)
        # subprocess.run(command) # instant return
        # Utils.run_simple(self.display, command)
        Utils.run_stdout(self.display, command)

    def commit(self):
        filenames = self.state.get_target_filenames(none_ok=True)
        # self.display.warn("git commit " + str(filenames))
        command = [ "git", "commit" ]
        command += filenames
        Utils.run_simple(self.display, command)

    def revert(self, filename):
        global logger
        logger = log_tools.logger_get(logger, "VC Git")
        logger.info("revert: " + filename)
        Utils.make_backup_cp(filename)
        command = [ "git", "checkout", filename ]
        subprocess.call(command)

    def add_p(self):
        global logger
        logger = log_tools.logger_get(logger, "VC Git")
        filenames = self.state.get_target_filenames()
        command = [ "git", "add", "-p" ]
        if len(filenames) == 0:
            filenames = [ "." ]
        command += filenames
        Utils.run_interactive_errors(command)

    def checkout_p(self):
        global logger
        logger = log_tools.logger_get(logger, "VC Git")
        filenames = self.state.get_target_filenames()
        command = [ "git", "checkout", "-p" ]
        if len(filenames) == 0:
            filenames = [ "." ]
        command += filenames
        logger.info("checkout -p: " + " ".join(filenames))
        for filename in filenames:
            Utils.make_backup_cp(filename)
        Utils.run_interactive_errors(command)

    def diff_cached(self):
        global logger
        logger = log_tools.logger_get(logger, "VC Git")
        filenames = self.state.get_target_filenames(none_ok=True)
        command = [ "git", "diff", "--cached", "--color=always" ]
        if len(filenames) == 0:
            filenames = [ "." ]
        command += filenames
        logger.info("diff --cached: " + " ".join(filenames))
        Utils.run_stdout(self.display, command)

    def log(self):
        filenames = self.state.get_target_filenames(none_ok=True)
        command = [ "git", "log" ]
        command += filenames
        global logger
        self.logger.info(command)
        Utils.run_stdout(self.state.display, command)

    def blame(self):
        filenames = self.state.get_target_filenames(none_ok=False)
        if len(filenames) != 1:
            self.state.display.warn("Blame requires 1 file!")
            return
        command = [ "git", "blame" ]
        command += filenames
        global logger
        self.logger.info(command)
        Utils.run_stdout(self.state.display, command)

    def reset_head(self):
        global logger
        logger = log_tools.logger_get(logger, "VC Git")
        filenames = self.state.get_target_filenames(none_ok=True)
        for filename in filenames:
            logger.info("reset head: " + filename)
            Utils.make_backup_cp(filename)
        command = [ "git", "reset", "HEAD" ]
        command += filenames
        self.logger.info(command)
        subprocess.call(command)

    def reset_patch(self):
        global logger
        logger = log_tools.logger_get(logger, "VC Git")
        filenames = self.state.get_target_filenames(none_ok=True)
        for filename in filenames:
            logger.info("reset patch: " + filename)
            Utils.make_backup_cp(filename)
        command = [ "git", "reset", "--patch" ]
        command += filenames
        self.logger.info(command)
        Utils.run_interactive_errors(command)
