# Copyright (c) conda-store development team. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from traitlets import Callable, Dict
from traitlets.config import LoggingConfigurable


class ContainerRegistry(LoggingConfigurable):
    container_registries = Dict(
        {},
        help="(deprecated) Registries url to upload built container images with callable function to configure registry instance with credentials",
        config=True,
    )

    container_registry_image_name = Callable(
        help="(deprecated) Image name to assign to docker image pushed for particular registry",
        config=True,
    )

    container_registry_image_tag = Callable(
        help="(deprecated) Image name and tag to assign to docker image pushed for particular registry",
        config=True,
    )
