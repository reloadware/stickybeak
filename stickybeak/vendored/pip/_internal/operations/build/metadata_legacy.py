"""Metadata generation logic for legacy source distributions.
"""

import logging
import os

from stickybeak.vendored.pip._internal.exceptions import InstallationError
from stickybeak.vendored.pip._internal.utils.setuptools_build import make_setuptools_egg_info_args
from stickybeak.vendored.pip._internal.utils.subprocess import call_subprocess
from stickybeak.vendored.pip._internal.utils.temp_dir import TempDirectory
from stickybeak.vendored.pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from stickybeak.vendored.pip._internal.build_env import BuildEnvironment

logger = logging.getLogger(__name__);logger.disabled=True


def _find_egg_info(directory):
    # type: (str) -> str
    """Find an .egg-info subdirectory in `directory`.
    """
    filenames = [
        f for f in os.listdir(directory) if f.endswith(".egg-info")
    ]

    if not filenames:
        raise InstallationError(
            "No .egg-info directory found in {}".format(directory)
        )

    if len(filenames) > 1:
        raise InstallationError(
            "More than one .egg-info directory found in {}".format(
                directory
            )
        )

    return os.path.join(directory, filenames[0])


def generate_metadata(
    build_env,  # type: BuildEnvironment
    setup_py_path,  # type: str
    source_dir,  # type: str
    isolated,  # type: bool
    details,  # type: str
):
    # type: (...) -> str
    """Generate metadata using setup.py-based defacto mechanisms.

    Returns the generated metadata directory.
    """
    logger.debug(
        'Running setup.py (path:%s) egg_info for package %s',
        setup_py_path, details,
    )

    egg_info_dir = TempDirectory(
        kind="pip-egg-info", globally_managed=True
    ).path

    args = make_setuptools_egg_info_args(
        setup_py_path,
        egg_info_dir=egg_info_dir,
        no_user_config=isolated,
    )

    with build_env:
        call_subprocess(
            args,
            cwd=source_dir,
            command_desc='python setup.py egg_info',
        )

    # Return the .egg-info directory.
    return _find_egg_info(egg_info_dir)