---
description: Learn to conda-store as shebang in Unix systems
---

# Use conda-store as shebang

:::warning
This page is in active development, content may be inaccurate and incomplete.
:::

`conda-store` can be used as a
[shebang](<https://en.wikipedia.org/wiki/Shebang_(Unix)>) within Linux
allowing users to embed conda environments within scripts for
reproducibility. Basic usage is as follows. Notice that the
`conda-store run` command is just the normal usage of the command.

```shell
#!/usr/bin/env conda-store
#! conda-store run <namespace>/<environment-name>:<build-id> -- python

print('script running within the conda-store environment')
```

The first line must begin with the shebang `#!` along with ending in
`conda-store`. You cannot put arguments on the first line due to
limits in the shebang specification. Additional lines are then added
starting with `#! conda-store run ...` with are then used as arguments
to `conda-store run`.

The path to the script being run is always appended as the last
argument to the command so the example above is interpreted as:

```
conda-store run <namespace>/<environment-name>:<build-id> -- python <shebang-filename>
```

This feature was heavily inspired by [`nix-shell`
shebangs](https://nixos.wiki/wiki/Nix-shell_shebang).
