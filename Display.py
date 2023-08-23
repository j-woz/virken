
# DISPLAY PY

import time

import curses

from log_tools import logger_get


logger = None


class Display:

    def __init__(self, window):
        self.window = window
        self.error_result = ""
        # Rows unusable by menu content:
        self.overhead = 4  # VC.info + blank + (content) + blank + prompt
        global logger
        self.logger = logger_get(logger, "Display")

        # self.logger.debug("Display() ...")
        curses.noecho()
        curses.raw()
        curses.cbreak()
        self.window.keypad(True)
        self.window.clear()
        self.window.nodelay(False)
        cp = 142
        # Color 15 is bright white
        try:
            # When this fails, try TERM=vt100
            curses.init_pair(cp, curses.COLOR_BLACK, 15)
            a = curses.color_pair(cp)
            self.window.bkgd(" ", a)
        except:
            self.logger.info("could not initialize colors")

    def curses_stop(self):
        # UNUSED? 2023-08-23
        self.logger.info("curses_stop()")
        curses.nocbreak()
        # self.window.keypad(False)
        curses.echo()
        curses.endwin()

    def out(self, s):
        try:
            self.window.addstr(str(s))
            self.window.refresh()
        except Exception as e:
            self.logger.error(s)
            self.logger.error(str(e))
            self.logger.error("")
            self.error_result += str(e)
            time.sleep(4)
        self.window.refresh()

    def outln(self, s):
        self.out(s+"\n")

    def warn(self, msg, timeout=1):
        """ Display a warning message """
        height, width = self.window.getmaxyx()
        self.window.move(height-1, 1)
        warning = "warn: " + msg
        # Make sure it fits in the window
        # (4 characters for symbol below)
        warning = warning[0:width-2-4]
        self.window.addstr(warning)
        self.window.refresh()
        self.window.nodelay(True)
        interval = 0.25
        duration = 0
        tokens = [ "/", "-", "\\", "|" ]
        index = 0
        while duration < timeout:
            c = self.window.getch()
            if c != curses.ERR:
                break
            symbol = " [%s]" % tokens[index]
            self.window.addstr(symbol)
            self.window.refresh()
            index = (index + 1) % len(tokens)
            time.sleep(interval)
            duration += interval
            y, x = self.window.getyx()
            self.window.move(y, x-len(symbol))
        self.window.nodelay(False)

    def reset(self):
        self.window.clear()
        self.window.move(1,1)

    def ask1(self, prompt):
        """ Ask the user for a single character """
        self.logger.debug("ask1() '%s' ..." % prompt)
        height, width = self.window.getmaxyx()
        # Clear line:
        self.window.move(height-1, 1)
        self.window.addstr(" " * (width-2))
        # Draw prompt:
        self.window.move(height-1, 1)
        self.window.addstr(prompt, curses.A_BOLD)
        self.window.refresh()
        c = self.window.getkey()
        self.logger.debug("ask1() -> '%s'" % c)
        return c

    def ask(self, prompt):
        """ Ask the user for a string """
        self.logger.debug("ask() '%s' ..." % prompt)
        height, width = self.window.getmaxyx()
        # Clear line:
        self.window.move(height-1, 1)
        self.window.addstr(" " * (width-2))
        # Draw prompt:
        self.window.move(height-1, 1)
        self.window.addstr(prompt, curses.A_BOLD)
        self.window.refresh()
        response = ""
        while True:
            c = self.window.getkey()
            if c == "\n":
                break
            if c == "KEY_BACKSPACE":
                self.backspace()
                response = response[:-1]
                continue
            if len(c) > 1:  # Some other special key
                continue
            self.window.addstr(c)
            response += c
        self.logger.debug("ask() -> '%s'" % response)
        return response

    def at_bottom(self, msg, lift=2):
        height, width = self.window.getmaxyx()
        self.at(height-lift, 1, msg)

    def at(self, y, x, msg, attrs=None):
        self.window.move(y, x)
        if attrs is None:
            self.window.addstr(msg)
        else:
            self.window.addstr(msg, attrs)
        self.window.refresh()

    def title(self, msg):
        self.at(0, 1, msg, attrs=curses.A_BOLD)

    def menu_pointer(self, offset, index, on):
        # pointer is always of length 5
        msg = " ==> " if on else "     "
        self.at(2+index-offset, 1, msg)

    def menu_content(self, offset, index, msg):
        self.at(2+index-offset, 5, msg)

    def backspace(self):
        y, x = self.window.getyx()
        self.window.move(y, x-1)
        self.window.addstr(" ")
        self.window.move(y, x-1)
