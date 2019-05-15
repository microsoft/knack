# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from six import string_types as STRING_TYPES


_DEFAULT_PREVIEW_TAG = '(PREVIEW)'
_preview_kwarg_name = 'is_preview'


def resolve_preview_info(cli_ctx, name):

    def _get_command(name):
        return cli_ctx.invocation.commands_loader.command_table[name]

    def _get_command_group(name):
        return cli_ctx.invocation.commands_loader.command_group_table.get(name, None)

    preview_info = None
    try:
        command = _get_command(name)
        preview_info = getattr(command, _preview_kwarg_name, None)
    except KeyError:
        command_group = _get_command_group(name)
        group_kwargs = getattr(command_group, 'group_kwargs', None)
        if group_kwargs:
            preview_info = group_kwargs.get(_preview_kwarg_name, None)
    return preview_info


class ColorizedString(object):

    def __init__(self, message, color):
        import colorama
        self._message = message
        self._color = getattr(colorama.Fore, color.upper(), None)

    def __len__(self):
        return len(self._message)

    def __str__(self):
        import colorama
        if not self._color:
            return self._message
        return self._color + self._message + colorama.Fore.RESET


# pylint: disable=too-many-instance-attributes
class PreviewItem(object):

    def __init__(self, cli_ctx=None, object_type='', target=None, tag_func=None, message_func=None):
        """ Create a collection of deprecation metadata.

        :param cli_ctx: The CLI context associated with the deprecated item.
        :type cli_ctx: knack.cli.CLI
        :param object_type: A label describing the type of object being deprecated.
        :type: object_type: str
        :param target: The name of the object being deprecated.
        :type target: str
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

        def _default_get_message(self):
            return "This {} is in preview and may be altered or removed " \
                   "in the future without warning.".format(self.object_type)

        self._get_tag = tag_func or (lambda _: _DEFAULT_PREVIEW_TAG)
        self._get_message = message_func or _default_get_message

    def __deepcopy__(self, memo):
        import copy

        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            try:
                setattr(result, k, copy.deepcopy(v, memo))
            except TypeError:
                if k == 'cli_ctx':
                    setattr(result, k, self.cli_ctx)
                else:
                    raise
        return result

    def show_in_help(self):
        # TODO: read config file to see if preview items should be shown?
        return True

    @property
    def tag(self):
        """ Returns a tag object. """
        return ColorizedString(self._get_tag(self), 'cyan')

    @property
    def message(self):
        """ Returns a tuple with the formatted message string and the message length. """
        return ColorizedString(self._get_message(self), 'cyan')


class ImplicitPreviewItem(PreviewItem):

    def __init__(self, **kwargs):

        def get_implicit_preview_message(self):
            return "This {} is in preview because command group '{}' is in preview. " \
                   "It may be altered or removed without warning in a future release.".format(self.object_type, self.target)

        kwargs.update({
            'tag_func': lambda _: '',
            'message_func': get_implicit_preview_message
        })
        super(ImplicitPreviewItem, self).__init__(**kwargs)
