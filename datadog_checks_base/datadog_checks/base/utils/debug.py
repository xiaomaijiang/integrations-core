# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under Simplified BSD License (see LICENSE)
import inspect
import pdb
import sys


class Debugger(pdb.Pdb):
    """Modified debugger that assumes the existence of predefined break points."""

    def set_trace(self, frame=None):
        """See https://github.com/python/cpython/blob/b02774f42108aaf18eb19865472c8d5cd95b5f11/Lib/bdb.py#L319-L332"""
        self.reset()

        if frame is None:
            frame = sys._getframe().f_back

        while frame:
            frame.f_trace = self.trace_dispatch
            self.botframe = frame
            frame = frame.f_back

        # Automatically proceed to next break point
        self.set_continue()

        sys.settrace(self.trace_dispatch)


def debug_function(f, line=0, args=(), kwargs=None):
    line = int(line)

    if kwargs is None:
        kwargs = {}

    file_name = inspect.getfile(f)
    lines, def_line = inspect.getsourcelines(f)

    if line == 0:
        line = def_line + 1
    elif line == -1:
        line = def_line + len(lines) - 1
    else:
        start = def_line + 1
        stop = def_line + len(lines)

        if line not in range(start, stop):
            raise ValueError('Line {} is not part of the check method.'.format(line))
        elif not lines[line - def_line].strip():
            raise ValueError('Line {} is a blank line and therefore there is nothing to execute.'.format(line))

    debugger = Debugger()
    debugger.set_break(file_name, line)
    debugger.set_trace()

    f(*args, **kwargs)
