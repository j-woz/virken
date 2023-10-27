
# This is just a test

import subprocess
import time

import curses

global window
curses.use_env(True)

def main(window):
    while True:
        start(window)
        window.addstr("? ")
        window.refresh()
        c = window.getkey()
        window.addstr("c: " + c)
        if c == "q":
            break
        window.refresh()
        window.clear()
        time.sleep(2)
        window.move(3,3)
        window.addstr("HOWDY ")
        window.refresh()
        time.sleep(2)

        stop(window)
        subprocess.run([ "less", "file.txt"])
        start(window)
        window.addstr("done. press key...")
        window.refresh()
        c = window.getkey()
        stop(window)

def start(window):

    curses.noecho()
    curses.raw()
    curses.cbreak()
    window.keypad(True)
    window.clear()
    curses.start_color()
    cp = 5
    curses.init_pair(cp, curses.COLOR_BLACK, curses.COLOR_WHITE)
    a = curses.color_pair(cp)
    #sys.stderr.write(str(a)+"\n")
    window.bkgd(" ", a)

def stop(window):
    curses.nocbreak()
    window.keypad(False)
    curses.echo()
    curses.endwin()

from curses import wrapper
wrapper(main)
