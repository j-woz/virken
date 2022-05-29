
# VC BASE

import Utils


class vc_base:

    def __init__(self, root, state, logger):
        self.root = root
        self.state = state
        self.logger = logger

    def diff2(self):
        filenames = self.state.get_target_filenames(none_ok=True)
        if len(filenames) != 2:
            self.state.display.warn("Two-file diff requires two files!")
            return
        command = [ "diff" ]
        command += filenames
        global logger
        self.logger.info(command)
        Utils.run_stdout(self.state.display, command)
