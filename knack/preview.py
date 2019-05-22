# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from .util import ColorizedString

_PREVIEW_TAG = '[Preview]'
_preview_kwarg = 'preview_info'


def resolve_preview_info(cli_ctx, name):

    def _get_command(name):
        return cli_ctx.invocation.commands_loader.command_table[name]

    def _get_command_group(name):
        return cli_ctx.invocation.commands_loader.command_group_table.get(name, None)

    preview_info = None
    try:
        command = _get_command(name)
        preview_info = getattr(command, _preview_kwarg, None)
    except KeyError:
        command_group = _get_command_group(name)
        group_kwargs = getattr(command_group, 'group_kwargs', None)
        if group_kwargs:
            preview_info = group_kwargs.get(_preview_kwarg, None)
    return preview_info


# pylint: disable=too-many-instance-attributes
class PreviewItem(object):

    def __init__(self, cli_ctx=None, object_type='', target=None, tag_func=None, message_func=None):
        """ Create a collection of preview metadata.

        :param cli_ctx: The CLI context associated with the preview item.
        :type cli_ctx: knack.cli.CLI
        :param object_type: A label describing the type of object in preview.
        :type: object_type: str
        :param target: The name of the object in preview.
        :type target: str
        :param tag_func: Callable which returns the desired unformatted tag string for the preview item.
                         Omit to use the default.
        :type tag_func: callable
        :param message_func: Callable which returns the desired unformatted message string for the preview item.
                             Omit to use the default.
        :type message_func: callable
        """
        self.cli_ctx = cli_ctx
        self.object_type = object_type
        self.target = target

        def _default_get_message(self):
            return "This {} is in preview. It may be changed/removed in a future release.".format(self.object_type)

        self._get_tag = tag_func or (lambda _: _PREVIEW_TAG)
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

    # pylint: disable=no-self-use
    def hidden(self):
        return False

    def show_in_help(self):
        return not self.hidden()

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
            return "Command group '{}' is in preview. It may be changed/removed " \
                   "in a future release.".format(self.target)

        kwargs.update({
            'tag_func': lambda _: '',
            'message_func': get_implicit_preview_message
        })
        super(ImplicitPreviewItem, self).__init__(**kwargs)
