
# VC SVN

import os
import subprocess

from log_tools import TRACE
from vc_base import vc_base
from Entry import Entry
import Utils


class vc_svn(vc_base):

    def __init__(self, root, state, logger):
        self.name = "SVN"
        super().__init__(root, state, logger)
        self.info = None
        self.logger.info("vc_svn init")

    def get_info(self):
        """ When this is called, self.display may be None """
        if self.info is not None: return
        # Default:
        relative_url = "..."
        root_path = ""
        try:
            workdir = os.getcwd()
            os.chdir(self.root)
            p = subprocess.Popen(["svn", "info"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            while True:
                line = p.stdout.readline().decode('UTF-8')
                line = line.strip()
                if len(line) == 0:
                    break
                self.logger.log(TRACE, "read: " + line)
                if "W155010" in line:
                    print("svn info: W155010")
                    exit(1)
                if line.startswith("Repository Root"):
                    tokens = line.split(" ")
                    repo = tokens[2]
                # Relative URL does not work in
                #    SVN 1.7.14 (released 2013-11) (Stampede2 2022-04-27)
                #    SVN 1.7.14 (released 2013-11) (CLASSE    2022-11-05)
                # Leads to missing data in info line at top
                # Could be fixed with additional string arithmetic
                if line.startswith("Relative URL"):
                    tokens = line.split(" ")
                    relative_url = tokens[2][2:]  # Drop "^/"
                if line.startswith("Working Copy Root"):
                    tokens = line.split(" ")
                    root_path = tokens[4]
        except Exception as e:
            print(str(e))
        if repo is None:
            print("Could not find SVN info!")
            exit(1)
        self.logger.info("vc_svn.get_info: repo:    " + repo)
        self.logger.info("vc_svn.get_info: workdir: " + workdir)
        # Working directory as relative to root_path
        workrel = workdir[len(root_path):]
        if len(workrel) == 0: workrel = "."
        self.logger.info("vc_svn.get_info: workrel: " + workrel)
        self.info = repo + " " + relative_url + " " + workrel
        os.chdir(workdir)

    def status(self, ignores):
        results = [ "NULL" ]
        self.do_svn_status(ignores, results)
        self.check_dirs(results)
        self.find_stashes(results)
        self.state.table = results
        self.state.stale = False
        return results

    def do_svn_status(self, ignores, results):
        command = [ "svn", "status" ]
        if not ignores:
            command += [ "--no-ignore" ]
        Utils.log_command("status", command, logger=self.logger)
        p = subprocess.Popen(command,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        reo = self.state.glob_compile()  # regular expression object
        while True:
            line = p.stdout.readline().decode('UTF-8')
            line = line.strip()
            if len(line) == 0:
                break
            self.do_svn_status_line(reo, line, results)

    def do_svn_status_line(self, reo, line, results):
        extra = " "
        # self.state.display.warn("line: " + line)
        if line[3] == "+":
            extra = "+"
            line = line.replace("+", " ")
        tokens = str(line).split(" ")

        if len(tokens) != 8:
            return
        chars = tokens[0]
        name  = tokens[7]
        if self.state.glob_match(reo, name):
            flags = ""
            mark = self.state.get_mark(name)
            if self.state.is_executable(name):
                flags += "*"
            results.append(Entry(mark, chars+extra, name, flags))

    def check_dirs(self, results):
        """
        SVN does not report directories with a slash- fix that here
        """
        global logger
        for entry in results:
            self.logger.info(str(entry))
            if entry == "NULL": continue
            if os.path.isdir(entry.name):
                entry.name = entry.name+"/"

    def find_stashes(self, results):
        import re
        L = os.listdir()
        reo = re.compile(".*\\.stash$")
        for f in L:
            if not reo.search(f):
                continue
            size = os.path.getsize(f)
            if size == 0:
                continue
            mark = self.state.get_mark(f)
            results.append(Entry(mark, "S ", f))

    def add(self):
        filenames = self.state.get_selected_filenames()
        try:
            command = [ "svn", "add" ]
            command += filenames
            self.stale = True
            subprocess.call(command)
        except:
            # self.display.outln("command failed!")
            pass

    def diff(self):
        filenames = self.state.get_selected_filenames(none_ok=True)
        # self.display.warn("svn diff " + str(filenames),
        #                  timeout=len(filenames))
        command = [ "svn", "diff" ]
        command += filenames
        # subprocess.run(command)
        # Utils.run_page(display, command)
        global logger
        self.logger.info(command)
        Utils.run_stdout(self.state.display, command)

    def commit(self):
        filenames = self.state.get_selected_filenames(none_ok=True)
        # self.display.warn("svn commit " + str(filenames),
        #                timeout=len(filenames))
        command = [ "svn", "commit", "--" ]
        command += filenames
        # Utils.run_poll(self.display, command)
        # Utils.run_poll(display, command)
        # subprocess.run(command)
        Utils.run_stdout(self.state.display, command)

    def revert(self, filename):
        global logger
        self.logger.info("revert: " + filename)
        Utils.make_backup_cp(filename)
        command = [ "svn", "revert", filename ]
        subprocess.call(command)

    def log(self):
        filenames = self.state.get_selected_filenames(none_ok=True)
        if len(filenames) > 1:
            self.state.display.warn("Log requires 0 or 1 file(s)!")
            return
        command = [ "svn", "log" ]
        command += filenames
        global logger
        self.logger.info(command)
        Utils.run_stdout(self.state.display, command)

    def blame(self):
        filenames = self.state.get_selected_filenames(none_ok=False)
        if len(filenames) != 1:
            self.state.display.warn("Blame requires 1 file!")
            return
        command = [ "svn", "blame" ]
        command += filenames
        global logger
        self.logger.info(command)
        Utils.run_stdout(self.state.display, command)

    def resolved(self):
        filenames = self.state.get_selected_filenames(none_ok=False)
        command = [ "svn", "resolved" ]
        command += filenames
        global logger
        self.logger.info(command)
        Utils.run_stdout(self.state.display, command)
