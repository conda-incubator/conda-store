def logged_command(context, command, **kwargs):
    # This is here only for backward compatibility, new code should use the
    # run_command method instead of calling this function
    context.run_command(command, **kwargs)
