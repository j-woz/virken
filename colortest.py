
# More colors:
# https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html#256-colors

import curses, time

def f(window):
    curses.use_env(True)
    curses.noecho()
    curses.raw()
    curses.cbreak()
    window.keypad(True)
    window.clear()
    window.nodelay(False)
    # set_colors()
    c = 0
    # curses.start_color()
    done = False
    s = "start"

    window.addstr(5, 0, "COLORS: %i" % curses.COLORS)
    window.addstr(6, 0, "COLOR_PAIRS: %i" % curses.COLOR_PAIRS)
    s = window.getkey()
    window.clear()

    # color_pair(pair_number) -> attr

    std = 142
    curses.init_pair(std, curses.COLOR_BLACK, 15)
    a = curses.color_pair(std)
    window.bkgd(" ", a)

    for i in range(0, 25):
        for j in range(0, 10):
            cn = 0+c
            # curses.init_color(cn, 00, 500, 500)
            cp = (16+cn) % 256
            curses.init_pair(cp, curses.COLOR_BLACK, cn)  # curses.COLOR_WHITE
            a = curses.color_pair(cp)
            # sys.stderr.write(str(a)+"\n")
            # window.bkgd(" ", a)
            msg = "'%s' %3i _-_" % (s.strip(), c)
            window.addstr(j, 0, msg, a)
            window.refresh()
            # print(msg)
            c = c+1
            if c > 255:
                window.addstr(j+1, 0, "END")
                window.refresh()
                break
            # window.chgat(a)
        s = window.getkey()
        if s == "q":
            done = True
            break
        window.clear()
        if done: break


curses.wrapper(f)  # -> menu_action
