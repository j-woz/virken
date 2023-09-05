
# VCMENU

import datetime
import os

from pathlib import Path

from verctrl.vc_svn import vc_svn
from verctrl.vc_git import vc_git
from verctrl.vc_fs  import vc_fs

from verctrl.log_tools import TRACE, logger_init, logger_get

from verctrl.Display import Display
from verctrl.State   import State
import verctrl.Utils as Utils

display = None
state   = None

# Set by argparse
args_force_fs = False

logger = None


def main():

    global VC, state
    global logger

    init()
    parse_args(logger)

    state = State()
    set_vc(state, logger, args_force_fs)
    set_vc_info(state.VC, logger)

    load_settings(state)

    import curses
    curses.use_env(True)
    global menu_action
    menu_action = None

    # Main control loop:
    # Most actions fall out of the curses wrapper
    # so that the various tools (e.g., editors) can use curses.
    while True:
        # curses.wrapper() cannot return a value-
        #                  we set global menu_action
        logger.info("curses wrapper start...")
        curses.wrapper(show_menu)  # -> menu_action
        logger.info("curses wrapper stop.\n")
        if menu_action == MenuAction.EXIT:
            break
        logger.info("handle_action start...")
        handle_action(menu_action)
        logger.info("handle_action stop.\n")
    logger.info("EXIT.\n")


def init():
    import atexit
    atexit.register(report_error_outs)

    logger_init()
    global logger
    logger = logger_get(logger, "VERCTRL")
    logger.info("-----------------")
    logger.info("START: " + datetime.date.today().isoformat())


def parse_args(logger):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-F", "--force_fs", action="store_true",
                        help='Start in FS mode')
    parser.add_argument('directory', nargs='?', default=".",
                        help='Start in this directory')
    args = parser.parse_args()
    set_directory(args.directory, logger)
    if args.force_fs:
        global args_force_fs
        args_force_fs = True


def found(f):
    if f is None:
        return False
    if not os.path.exists(f):
        return False
    return True


def load_settings(state):
    config_dir  = Utils.getenv(["VERCTRL_CONFIG_DIR"])
    if not found(config_dir):
        config_home = Utils.getenv(["XDG_CONFIG_HOME"],
                                   default=os.getenv("HOME")+"/.config")
        config_dir = config_home+"/verctrl"
        if not found(config_dir):
            config_dir = os.getenv("HOME")+"/.verctrl"
            if not found(config_dir):
                return False
    load_fs_ignores(state, config_dir+"/fs-ignores.cfg")


def load_fs_ignores(state, cfg):
    if os.path.exists(cfg):
        state.fs_ignores = Utils.read_list(cfg)
    else:
        state.fs_ignores = []


def set_directory(directory, logger):
    try:
        os.chdir(directory)
    except:
        print("vcmenu: could not chdir to: " + directory)
        abort(logger)

    logger.info("PWD: " + os.getcwd())


def set_vc(state, logger, force_fs=False):
    """ Figure out what Version Control system we are using """
    global VC
    workdir = os.getcwd()
    p = Path(workdir)
    vc_string, root = detect_vc(p)
    logger.info("set_vc: " + vc_string)

    if vc_string == "FS" or force_fs:
        VC = vc_fs(root, state, logger)
    elif vc_string == "SVN":
        VC = vc_svn(root, state, logger)
    elif vc_string == "GIT":
        VC = vc_git(root, state, logger)
    state.VC = VC


def detect_vc(p):
    """ p: A Path.  Return TYPE, ROOT """
    for level in range(1, 20):
        svndir = p / ".svn"
        if svndir.exists():
            return "SVN", p
        gitdir = p / ".git"
        if gitdir.exists():
            return "GIT", p
        parent = p.parent.resolve()
        if parent == p:  # Root "/" or some error
            return "FS", None
        p = parent

    # Too many levels
    return "NONE"


def set_vc_info(VC, logger):
    try:
        logger.info("VC: " + VC.name)
        VC.get_info()
    except Exception as e:
        logger.info("VC: ERROR:\n" + str(e))
        print("Error checking version control: " + str(e))
        raise
        abort(logger)


def handle_action(action):
    """ These always happen outside the curses wrapper """
    global logger, state
    logger.debug("handle action: " + str(action))
    if action == MenuAction.HELP:
        help()
    elif action == MenuAction.COMMIT:
        state.VC.commit()
    elif action == MenuAction.EDIT:
        state.edit()
    elif action == MenuAction.EXAMINE:
        state.examine()
    elif action == MenuAction.DIFF:
        state.VC.diff()
    elif action == MenuAction.DIFF2:
        state.VC.diff2()
    elif action == MenuAction.LOG:
        state.VC.log()
    elif action == MenuAction.BLAME:
        state.VC.blame()
    elif action == MenuAction.GIT_DIFF_CACHED:
        state.VC.diff_cached()
    elif action == MenuAction.GIT_ADD_P:
        state.VC.add_p()
        state.stale = True
    elif action == MenuAction.GIT_CHECKOUT_P:
        state.VC.checkout_p()
        state.stale = True
    elif action == MenuAction.GIT_DIFF_CACHED:
        state.VC.diff_cached()
    elif action == MenuAction.GIT_RESET_HEAD:
        state.VC.reset_head()
        state.stale = True
    elif action == MenuAction.GIT_RESET_PATCH:
        state.VC.reset_patch()
        state.stale = True
    elif action == MenuAction.SVN_STASH_POP:
        state.stash_pop()
        state.stale = True
    elif action == MenuAction.SVN_STASH_PUSH:
        state.stash_push()
        state.stale = True
    elif action == MenuAction.SVN_RESOLVED:
        state.VC.resolved()
        state.stale = True
    else:
        raise(Exception("Unknown action! " + str(action)))


# def set_colors():
#     c = 5
#     curses.init_pair(c, curses.COLOR_BLACK, curses.COLOR_WHITE)
#     a = curses.color_pair(c)
#     # sys.stderr.write(str(a)+"\n")
#     window.bkgd(" ", a)


from enum import Enum


class MenuAction(Enum):
    LOOP    = 1    # Normal case, loop
    ARROW   = 2    # Just update the menu pointer
    HELP    = 100
    EDIT    = 101
    EXAMINE = 102
    DIFF    = 103
    DIFF2   = 104
    COMMIT  = 105
    LOG     = 106
    BLAME   = 107
    GIT_ADD_P       = 201
    GIT_CHECKOUT_P  = 202
    GIT_DIFF_CACHED = 203
    GIT_RESET_HEAD  = 204
    GIT_RESET_PATCH = 205
    SVN_STASH_POP   = 314
    SVN_STASH_PUSH  = 315
    SVN_RESOLVED    = 320
    EXIT    = 1000  # Exit the program.


def show_menu(window):
    global display, state, logger, menu_action
    display = Display(window)
    state.VC.display = display
    state.display    = display

    result = None
    while True:
        if result == MenuAction.ARROW:
            # ARROW means skip the full redraw
            result = MenuAction.LOOP
        else:
            prefix = state.show()
        c = display.ask1("%s %s: " % (prefix, state.VC.name))
        if c != " ":
            c = c.strip()
        logger.debug("key: " + c)
        if c == "q":
            menu_action = MenuAction.EXIT
            return
        result = handle_char(c)
        if state.chdir:
            set_vc(state, logger)
            set_vc_info(state.VC, logger)
        if result != MenuAction.LOOP and result != MenuAction.ARROW:
            menu_action = result
            return
        logger.debug("LOOP")


def handle_char(c):
    """ Respond to a user input command """
    global state, display, logger
    result = MenuAction.LOOP
    if c == "":
        logger.debug("refresh")
        state.stale = True
    elif c == "KEY_RESIZE":
        logger.debug("resize")
        state.stale = True
    elif Utils.is_int(c):
        state.current = int(c)
    elif c == " ":
        state.select()
    elif c == "a":
        state.VC.add()
        state.stale = True
    elif c == "A":
        state.select_all()
    elif c == "b":
        result = MenuAction.BLAME
    elif c == "c":
        state.cd()
    elif c == "C":
        result = MenuAction.COMMIT
        state.stale = True
    elif c == "d":
        result = MenuAction.DIFF
    elif c == "D":
        result = MenuAction.DIFF2
    elif c == "e":
        result = MenuAction.EXAMINE
    elif c == "F":
        if type(state.VC) == vc_fs:
            set_vc(state, logger)
        else:
            set_vc(state, logger, force_fs=True)
        set_vc_info(state.VC, logger)
        state.stale = True
    elif c == "g":
        state.glob_ask()
    elif c == "G":
        result = git_subcmd()
    elif c == "h":
        display.warn("Help! ")
        result = MenuAction.HELP
    elif c == "j":
        state.jump_ask()
    elif c == "I":
        state.toggle_ignores()
    elif c == "k":
        state.mark_backup_mv()
    elif c == "K":
        state.mark_backup_cp()
    elif c == "l":
        state.marks_load(force=True)
    elif c == "L":
        result = MenuAction.LOG
    elif c == "s":
        state.marks_save()
    elif c == "S":
        result = svn_subcmd()
    elif c == "t":
        state.toggle_stats()
    elif c == "v":
        result = MenuAction.EDIT
        state.stale = True
    elif c == "V":
        state.revert()
        state.stale = True
    elif c == "w":
        state.search()
    elif c == "W":
        state.toggle_worddiff()
    elif c == "x":
        state.mark_delete()
        state.key_down()
    elif c == "X":
        state.expunge()
    elif c == "z":
        state.select_zero()
    elif c == "KEY_UP" or c == "p":
        state.key_up()
        result = MenuAction.ARROW
    elif c == "KEY_DOWN" or c == "n":
        state.key_down()
        result = MenuAction.ARROW
    elif c == "P" or c == "KEY_PPAGE":
        state.page_up()
    elif c == "N" or c == "KEY_NPAGE":
        state.page_down()
    elif c == ">":
        state.cd()
    elif c == "^":
        state.cd_up()
    else:
        display.warn("unknown character: '%s'" % c)

    logger.debug("end of handle")
    return result


def help():
    vcmenu_home = os.getenv("VCMENU_HOME")
    Utils.pager_files(display, [ vcmenu_home + "/etc/help.txt" ] )


def git_subcmd():
    global display
    c = display.ask1("git subcmd: " +
                     "( ) cancel " +
                     "(a) add -p " +
                     "(c) checkout -p " +
                     "(d) diff --cached " +
                     "(r) reset ")
    if   c == "a":
        return MenuAction.GIT_ADD_P
    elif c == "c":
        return MenuAction.GIT_CHECKOUT_P
    elif c == "d":
        return MenuAction.GIT_DIFF_CACHED
    elif c == "r":
        return git_subcmd_reset()
    else:
        return MenuAction.LOOP


def git_subcmd_reset():
    global display
    c = display.ask1("git reset: " +
                     "( ) cancel " +
                     "(h) HEAD " +
                     "(p) patch ")
    if   c == "h":
        return MenuAction.GIT_RESET_HEAD
    elif c == "p":
        return MenuAction.GIT_RESET_PATCH
    else:
        return MenuAction.LOOP


def svn_subcmd():
    global display
    c = display.ask1("svn subcmd: "    +
                     "( ) cancel "     +
                     "(u) stash-push " +
                     "(o) stash-pop "  +
                     "(r) resolved ")
    if   c == "u":
        return MenuAction.SVN_STASH_PUSH
    elif c == "o":
        return MenuAction.SVN_STASH_POP
    elif c == "r":
        return MenuAction.SVN_RESOLVED
    else:
        return MenuAction.LOOP


def report_error_outs():
    global state
    if state is None:
        return
    if display is not None and display.error_result != "":
        print("")
        print("ERROR RESULTS:")
        print(display.error_result)
        print("")


def abort(logger):
    logger.fatal("ABORT!\n")
    exit(1)


# Debugging entry point
# E.g., bin/verctrl-debug
if __name__ == '__main__':
    main()
