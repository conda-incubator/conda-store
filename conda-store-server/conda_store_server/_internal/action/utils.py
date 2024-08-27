# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.


def logged_command(context, command, **kwargs):
    # This is here only for backward compatibility, new code should use the
    # run_command method instead of calling this function
    context.run_command(command, **kwargs)
