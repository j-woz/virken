
# UTILS PY

import os, sys
import select, subprocess, tempfile
from subprocess import DEVNULL, PIPE

import log_tools

logger = None

vcmenu_tmp = None
def tmp():
    # returns fp, tmpfilename
    global vcmenu_tmp
    if vcmenu_tmp == None:
        vcmenu_tmp = os.getenv("VCMENU_TMP")
    return tempfile.mkstemp(suffix=".txt",
                            prefix=vcmenu_tmp+"/utils-")

def getenv(L, default=None):
    for entry in L:
        v = os.getenv(entry)
        if v != None and len(v) > 0:
            return v
    return default

pager = None
def get_pager():
    """ returns: list of tokens to launch pager in the shell: """
    """ e.g. [ "less", "-f" ]  """
    """ NOTE: This list should be treated as read-only- """
    """       use list.copy() """
    global pager
    if pager != None:
        return pager
    v = getenv([ "VCMENU_PAGER", "PAGER" ], default="less --force")
    if v != None:
        pager = v.split()
    return pager

editor = None
def get_editor():
    """ returns: list of tokens to launch editor in the shell: """
    """ e.g. [ "emacs", "-nw" ]  """
    global editor
    if editor != None:
        return editor
    v = getenv([ "VCMENU_EDITOR", "EDITOR"], default="vi")
    if v != None:
        editor = v.split()
    return editor

def run_page(display, command):
    log_command("run_page", command)
    fp = tempfile.NamedTemporaryFile(mode="wb+", buffering=0)
    subprocess.run(command, stdout=fp, stderr=fp)
    pager_files(display, [fp.name])
    display.window.keypad(True)

def run_simple(display, command):
    # return True on success, else False
    #         auto-displays errors
    # Discards stdout!
    errs = run_stderr(command)
    if errs != None:
        pager_str(errs)
        sys.stderr.write(str(command) + "\n")
        sys.stderr.write(errs + "\n\n")
        return False
    return True

def run_stdout(display, command):
    # fp = tempfile.TemporaryFile(mode="w+", buffering=1)
    fp = tempfile.NamedTemporaryFile(mode="wb+", buffering=0)
    log_command("run_stdout", command)
    cp = subprocess.run(command, stdout=fp, stderr=fp)
    log_command("run_stdout", command, done=True)
    fp.seek(0)
    # message = fp.read()
    # pager_str(display, message)
    pager_files(display, [fp.name])

def run_stderr(command):
    '''  This discards stdout!  '''
    fp = tempfile.TemporaryFile(mode="w+", buffering=1)
    # sys.stderr.write(str(command) + "\n")
    log_command("run_stderr", command)
    cp = subprocess.run(command, stdout=DEVNULL, stderr=fp)
    log_command("run_stderr", command, done=True)
    errs = None
    if cp.returncode != 0:
        fp.seek(0)
        errs = "COMMAND FAILED: " + str(command) + "\n\n"
        while True:
            s = fp.readline()
            if s == "":
                break
            errs += s + "\n"
    return errs

def run_interactive_errors(command):
    fp = tempfile.NamedTemporaryFile(mode="w+", buffering=1)
    log_command("run_interactive_errors", command)
    cp = subprocess.run(command, stderr=fp)
    log_command("run_interactive_errors", command, done=True)

    fp.seek(0)
    errs = ""
    while True:
        s = fp.readline()
        if s == "":
            break
        errs += s + "\n"

    if len(errs) > 0:
        message = "COMMAND FAILED: " + str(command) + "\n" + \
                  "RETURN CODE: " + str(cp.returncode) + \
                  errs
        pager_str(errs)
    return errs

def delay_incr(t):
    max_delay = 1.0
    if t == 0:
        t = 0.001
    elif t >= max_delay:
        t = max_delay
    else:
        t = t*2
        print("%0.3f" % t)
    return t

def run_poll(display, command, page_output=False):
    fp = tempfile.NamedTemporaryFile(mode="wb+", buffering=0)
    P = subprocess.Popen(command, stdout=PIPE, stderr=fp, bufsize=0)
    delay = 0.0
    while True:
        # print("poll")
        rc = P.poll()
        if rc is not None:
            break
        r,w,x = select.select([P.stdout,], [], [], delay)
        if len(r) == 0:
            delay = delay_incr(delay)
            continue
        m = r[0].read()
        n = len(m)
        if n == 0:
            delay = delay_incr(delay)
            continue
        s = m.decode("UTF-8")
        # display.out(s)
        sys.stdout.write("<"+str(n)+":"+s+"> ")
        sys.stdout.flush()
        # print(s)
        delay = 0
    errs = None
    if P.returncode != 0:
        fp.seek(0)
        errs = "COMMAND FAILED: " + str(command) + "\n\n"
        while True:
            s = fp.readline()
            if s == "":
                break
            errs += s + "\n"
        return False
    if page_output:
        pager_files(display, [fp.name])
    return True

def pager_str(message):
    command = get_pager()
    log_command("pager_str", command)
    cp = subprocess.run(command, input=message.encode("UTF-8"))
    if cp.returncode != 0:
        logger.warn("pager failed!")

def pager_files(display, files):
    assert(type(files) == list)
    command = get_pager().copy()
    # sys.stderr.write(str(command) + "\n")
    command += files
    log_command("pager_files", command)
    cp = subprocess.run(command)
    if cp.returncode != 0:
        logger = log_tools.logger_get(None, "Utils")
        logger.warn("pager_files(): command returned code=%i : %s" %
                    (cp.returncode, str(command)))
        return False
    display.window.keypad(True)
    return True

def editor_files(display, files):
    command  = get_editor()
    # sys.stderr.write(str(command) + "\n")
    command += files
    log_command("editor_files", command)
    subprocess.run(command)
    display.window.keypad(True)

def log_command(func, command, logger=None, done=False):
    logger = log_tools.logger_get(logger, "Utils")
    # logger.info(str(command))
    suffix = " done." if done else " ..."
    logger.info(func + "(): " + "command: " +
                " ".join(command) + suffix)

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def plural(c):
    if c == 1:
        return ""
    return "s"

def make_backup_cp(filename):
    backup = filename + ".bac~"
    command = [ "cp", "--backup=numbered", filename, backup ]
    log_command("make_backup_cp", command)
    c = subprocess.call(command)

def make_backup_mv(filename):
    backup = filename + ".bak~"
    command = [ "mv", "--backup=numbered", filename, backup ]
    log_command("make_backup_mv", command)
    subprocess.call(command)

def read_list(filename):
    result = []
    with open(filename) as fp:
        while True:
            line = fp.readline()
            if len(line) == 0: break
            tokens = line.split("#")
            text = tokens[0]
            text = text.strip()
            if len(text) == 0:
                continue
            result.append(text)
    return result

def bytes_human(b):
    if b < 10000:
        return "%6i  B" % b
    elif b < 1024*1024:
        return "%6.1f KB" % (b/1024)
    else:
        return "%6.1f MB" % (b/(1024*1024))
