# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import colorama
from six import string_types as STRING_TYPES

from knack.log import get_logger

logger = get_logger(__name__)


DEFAULT_DEPRECATED_TAG = '[Deprecated]'


def resolve_deprecate_info(cli_ctx, name):

    def _get_command(name):
        return cli_ctx.invocation.commands_loader.command_table[name]

    def _get_command_group(name):
        return cli_ctx.invocation.commands_loader.command_group_table.get(name, None)

    deprecate_info = None
    try:
        command = _get_command(name)
        deprecate_info = getattr(command, 'deprecate_info', None)
    except KeyError:
        command_group = _get_command_group(name)
        group_kwargs = getattr(command_group, 'group_kwargs', None)
        if group_kwargs:
            deprecate_info = group_kwargs.get('deprecate_info', None)
    return deprecate_info


class ColorizedString(object):

    def __init__(self, message, color):
        self._message = message
        self._color = getattr(colorama.Fore, color.upper(), None)

    def __len__(self):
        return len(self._message)

    def __str__(self):
        if not self._color:
            return self._message
        return self._color + self._message + colorama.Fore.RESET


# pylint: disable=too-many-instance-attributes
class Deprecated(object):

    @staticmethod
    def ensure_new_style_deprecation(cli_ctx, kwargs, object_type):
        """ Helper method to make the previous string-based deprecate_info kwarg
            work with the new style. """
        deprecate_info = kwargs.get('deprecate_info', None)
        if isinstance(deprecate_info, Deprecated):
            deprecate_info.object_type = object_type
        elif isinstance(deprecate_info, STRING_TYPES):
            deprecate_info = Deprecated(cli_ctx, redirect=deprecate_info, object_type=object_type)
        kwargs['deprecate_info'] = deprecate_info
        return deprecate_info

    def __init__(self, cli_ctx=None, object_type='', target=None, redirect=None, hide=False, expiration=None,
                 tag_func=None, message_func=None):
        """ Create a collection of deprecation metadata.

        :param cli_ctx: The CLI context associated with the deprecated item.
        :type cli_ctx: knack.cli.CLI
        :param object_type: A label describing the type of object being deprecated.
        :type: object_type: str
        :param target: The name of the object being deprecated.
        :type target: str
        :param redirect: The alternative to redirect users to in lieu of the deprecated item. If omitted it, there is
                         no alternative.
        :type redirect: str
        :param hide: A boolean or CLI version at or above-which the deprecated item will no longer appear
                     in help text, but will continue to work. Warnings will be displayed if the deprecated
                     item is used.
        :type hide: bool OR str
        :param expiration: The CLI version at or above-which the deprecated item will no longer work.
        :type expiration: str
        :param tag_func: Callable which returns the desired unformatted tag string for the deprecated item.
                         Omit to use the default.
        :type tag_func: callable
        :param message_func: Callable which returns the desired unformatted message string for the deprecated item.
                             Omit to use the default.
        :type message_func: callable
        """
        self.cli_ctx = cli_ctx
        self.object_type = object_type
        self.target = target
        self.redirect = redirect
        self.hide = hide
        self.expiration = expiration

        def _default_get_message(self):
            line1 = "This {} has been deprecated and will be removed ".format(self.object_type)
            if self.expiration:
                line1 += "in version '{}'.".format(self.expiration)
            else:
                line1 += 'in a future release.'
            lines = [line1]
            if self.redirect:
                lines.append("Use '{}' instead.".format(self.redirect))
            return ' '.join(lines)

        self._get_tag = tag_func or (lambda _: DEFAULT_DEPRECATED_TAG)
        self._get_message = message_func or _default_get_message

    # pylint: disable=no-self-use
    def _version_less_than_or_equal_to(self, v1, v2):
        """ Returns true if v1 <= v2. """
        if v1 == v2:
            return True
        v1_comps = v1.split('.')
        v2_comps = v2.split('.')
        if len(v1_comps) != len(v2_comps):
            from knack.util import CLIError
            raise CLIError("Unable to compare version '{}' to version '{}'. Check version format.".format(v1, v2))
        for i, _ in enumerate(v1_comps):
            if v1_comps[i] < v2_comps[i]:
                return True
            elif v1_comps[i] > v2_comps[i]:
                return False
        return False

    def expired(self):
        if self.expiration:
            cli_version = self.cli_ctx.get_cli_version()
            return self._version_less_than_or_equal_to(self.expiration, cli_version)
        return False

    def hidden(self):
        hidden = False
        if isinstance(self.hide, bool):
            hidden = self.hide
        elif isinstance(self.hide, STRING_TYPES):
            cli_version = self.cli_ctx.get_cli_version()
            hidden = self._version_less_than_or_equal_to(self.hide, cli_version)
        return hidden

    def show_in_help(self):
        return not self.hidden() and not self.expired()

    @property
    def tag(self):
        """ Returns a tag object. """
        return ColorizedString(self._get_tag(self), 'yellow')

    @property
    def message(self):
        """ Returns a tuple with the formatted message string and the message length. """
        return ColorizedString(self._get_message(self), 'yellow')


class ImplicitDeprecated(Deprecated):

    def __init__(self, **kwargs):

        def get_implicit_deprecation_message(self):
            line1 = "This {} is implicitly deprecated because command group '{}' is deprecated " \
                    "and will be removed ".format(self.object_type, self.target)
            if self.expiration:
                line1 += "in version '{}'.".format(self.expiration)
            else:
                line1 += 'in a future release.'
            lines = [line1]
            if self.redirect:
                lines.append("Use '{}' instead.".format(self.redirect))
            return ' '.join(lines)

        kwargs.update({
            'tag_func': lambda _: '',
            'message_func': get_implicit_deprecation_message
        })
        super(ImplicitDeprecated, self).__init__(**kwargs)
