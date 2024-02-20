import subprocess


def logged_command(context, command, **kwargs):
    context.log.info(f"Running command: {' '.join(command)}")
    context.log.info(
        subprocess.check_output(
            command, stderr=subprocess.STDOUT, encoding="utf-8", **kwargs
        )
    )
