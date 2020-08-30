from __future__ import absolute_import

import logging
import sys
import textwrap
from collections import OrderedDict

from stickybeak._priv.pip._vendor import pkg_resources
from stickybeak._priv.pip._vendor.packaging.version import parse as parse_version
# NOTE: XMLRPC Client is not annotated in typeshed as on 2017-07-17, which is
#       why we ignore the type on this import
from stickybeak._priv.pip._vendor.six.moves import xmlrpc_client  # type: ignore

from stickybeak._priv.pip._internal.cli.base_command import Command
from stickybeak._priv.pip._internal.cli.req_command import SessionCommandMixin
from stickybeak._priv.pip._internal.cli.status_codes import NO_MATCHES_FOUND, SUCCESS
from stickybeak._priv.pip._internal.exceptions import CommandError
from stickybeak._priv.pip._internal.models.index import PyPI
from stickybeak._priv.pip._internal.network.xmlrpc import PipXmlrpcTransport
from stickybeak._priv.pip._internal.utils.compat import get_terminal_size
from stickybeak._priv.pip._internal.utils.logging import indent_log
from stickybeak._priv.pip._internal.utils.misc import get_distribution, write_output
from stickybeak._priv.pip._internal.utils.typing import MYPY_CHECK_RUNNING

if MYPY_CHECK_RUNNING:
    from optparse import Values
    from typing import List, Dict, Optional
    from typing_extensions import TypedDict
    TransformedHit = TypedDict(
        'TransformedHit',
        {'name': str, 'summary': str, 'versions': List[str]},
    )

logger = logging.getLogger(__name__);logger.disabled=True


class SearchCommand(Command, SessionCommandMixin):
    """Search for PyPI packages whose name or summary contains <query>."""

    usage = """
      %prog [options] <query>"""
    ignore_require_venv = True

    def add_options(self):
        # type: () -> None
        self.cmd_opts.add_option(
            '-i', '--index',
            dest='index',
            metavar='URL',
            default=PyPI.pypi_url,
            help='Base URL of Python Package Index (default %default)')

        self.parser.insert_option_group(0, self.cmd_opts)

    def run(self, options, args):
        # type: (Values, List[str]) -> int
        if not args:
            raise CommandError('Missing required argument (search query).')
        query = args
        pypi_hits = self.search(query, options)
        hits = transform_hits(pypi_hits)

        terminal_width = None
        if sys.stdout.isatty():
            terminal_width = get_terminal_size()[0]

        print_results(hits, terminal_width=terminal_width)
        if pypi_hits:
            return SUCCESS
        return NO_MATCHES_FOUND

    def search(self, query, options):
        # type: (List[str], Values) -> List[Dict[str, str]]
        index_url = options.index

        session = self.get_default_session(options)

        transport = PipXmlrpcTransport(index_url, session)
        pypi = xmlrpc_client.ServerProxy(index_url, transport)
        hits = pypi.search({'name': query, 'summary': query}, 'or')
        return hits


def transform_hits(hits):
    # type: (List[Dict[str, str]]) -> List[TransformedHit]
    """
    The list from pypi is really a list of versions. We want a list of
    packages with the list of versions stored inline. This converts the
    list from pypi into one we can use.
    """
    packages = OrderedDict()  # type: OrderedDict[str, TransformedHit]
    for hit in hits:
        name = hit['name']
        summary = hit['summary']
        version = hit['version']

        if name not in packages.keys():
            packages[name] = {
                'name': name,
                'summary': summary,
                'versions': [version],
            }
        else:
            packages[name]['versions'].append(version)

            # if this is the highest version, replace summary and score
            if version == highest_version(packages[name]['versions']):
                packages[name]['summary'] = summary

    return list(packages.values())


def print_results(hits, name_column_width=None, terminal_width=None):
    # type: (List[TransformedHit], Optional[int], Optional[int]) -> None
    if not hits:
        return
    if name_column_width is None:
        name_column_width = max([
            len(hit['name']) + len(highest_version(hit.get('versions', ['-'])))
            for hit in hits
        ]) + 4

    installed_packages = [p.project_name for p in pkg_resources.working_set]
    for hit in hits:
        name = hit['name']
        summary = hit['summary'] or ''
        latest = highest_version(hit.get('versions', ['-']))
        if terminal_width is not None:
            target_width = terminal_width - name_column_width - 5
            if target_width > 10:
                # wrap and indent summary to fit terminal
                summary_lines = textwrap.wrap(summary, target_width)
                summary = ('\n' + ' ' * (name_column_width + 3)).join(
                    summary_lines)

        line = '{name_latest:{name_column_width}} - {summary}'.format(
            name_latest='{name} ({latest})'.format(**locals()),
            **locals())
        try:
            write_output(line)
            if name in installed_packages:
                dist = get_distribution(name)
                assert dist is not None
                with indent_log():
                    if dist.version == latest:
                        write_output('INSTALLED: %s (latest)', dist.version)
                    else:
                        write_output('INSTALLED: %s', dist.version)
                        if parse_version(latest).pre:
                            write_output('LATEST:    %s (pre-release; install'
                                         ' with "pip install --pre")', latest)
                        else:
                            write_output('LATEST:    %s', latest)
        except UnicodeEncodeError:
            pass


def highest_version(versions):
    # type: (List[str]) -> str
    return max(versions, key=parse_version)
