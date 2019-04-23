# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import sys
import stat
from six.moves import configparser

from .util import ensure_dir

_UNSET = object()


def get_config_parser():
    return configparser.ConfigParser() if sys.version_info.major == 3 else configparser.SafeConfigParser()


class CLIConfig(object):
    _BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    _DEFAULT_CONFIG_ENV_VAR_PREFIX = 'CLI'
    _DEFAULT_CONFIG_DIR = os.path.join('~', '.{}'.format('cli'))
    _DEFAULT_CONFIG_FILE_NAME = 'config'
    _CONFIG_DEFAULTS_SECTION = 'defaults'

    def __init__(self, config_dir=None, config_env_var_prefix=None, config_file_name=None, use_local_config=None):
        """ Manages configuration options available in the CLI

        :param config_dir: The directory to store config files
        :type config_dir: str
        :param config_env_var_prefix: The prefix for config environment variables
        :type config_env_var_prefix: str
        :param config_file_name: The name given to the config file to be created
        :type config_file_name: str
        """
        config_dir = config_dir or CLIConfig._DEFAULT_CONFIG_DIR
        ensure_dir(config_dir)
        config_env_var_prefix = config_env_var_prefix or CLIConfig._DEFAULT_CONFIG_ENV_VAR_PREFIX
        env_var_prefix = '{}_'.format(config_env_var_prefix.upper())
        default_config_dir = os.path.expanduser(config_dir)
        self.config_dir = os.environ.get('{}CONFIG_DIR'.format(env_var_prefix), default_config_dir)
        configuration_file_name = config_file_name or CLIConfig._DEFAULT_CONFIG_FILE_NAME
        self.config_path = os.path.join(self.config_dir, configuration_file_name)
        self._env_var_format = '{}{}'.format(env_var_prefix, '{section}_{option}')
        self.defaults_section_name = CLIConfig._CONFIG_DEFAULTS_SECTION
        self.use_local_config = use_local_config
        self._config_file_chain = []
        current_dir = os.getcwd()
        config_dir_name = os.path.basename(self.config_dir)
        while current_dir:
            current_config_dir = os.path.join(current_dir, config_dir_name)
            # Stop if already in the default .azure
            if (os.path.normcase(os.path.normpath(current_config_dir)) ==
                    os.path.normcase(os.path.normpath(self.config_dir))):
                break
            if os.path.isdir(current_config_dir):
                self._config_file_chain.append(_ConfigFile(current_config_dir,
                                                           os.path.join(current_config_dir, configuration_file_name)))
            # Stop if already in root drive
            if current_dir == os.path.dirname(current_dir):
                break
            current_dir = os.path.dirname(current_dir)
        self._config_file_chain.append(_ConfigFile(self.config_dir, self.config_path))

    def env_var_name(self, section, option):
        return self._env_var_format.format(section=section.upper(),
                                           option=option.upper())

    def has_option(self, section, option):
        if self.env_var_name(section, option) in os.environ:
            return True
        config_files = self._config_file_chain if self.use_local_config else self._config_file_chain[-1:]
        return bool(next((f for f in config_files if f.has_option(section, option)), False))

    def get(self, section, option, fallback=_UNSET):
        env = self.env_var_name(section, option)
        if env in os.environ:
            return os.environ[env]
        last_ex = None
        for config in self._config_file_chain if self.use_local_config else self._config_file_chain[-1:]:
            try:
                return config.get(section, option)
            except (configparser.NoSectionError, configparser.NoOptionError) as ex:
                last_ex = ex

        if fallback is _UNSET:
            raise last_ex  # pylint:disable=raising-bad-type
        return fallback

    def items(self, section):
        import re
        pattern = self.env_var_name(section, '.+')
        candidates = [(k.split('_')[-1], os.environ[k], k) for k in os.environ.keys() if re.match(pattern, k)]
        result = {c[0]: c for c in candidates}
        for config in self._config_file_chain if self.use_local_config else self._config_file_chain[-1:]:
            try:
                entries = config.items(section)
                for name, value in entries:
                    if name not in result:
                        result[name] = (name, value, config.config_path)
            except (configparser.NoSectionError, configparser.NoOptionError):
                pass
        return [{'name': name, 'value': value, 'source': source} for name, value, source in result.values()]

    def getint(self, section, option, fallback=_UNSET):
        return int(self.get(section, option, fallback))

    def getfloat(self, section, option, fallback=_UNSET):
        return float(self.get(section, option, fallback))

    def getboolean(self, section, option, fallback=_UNSET):
        val = str(self.get(section, option, fallback))
        if val.lower() not in CLIConfig._BOOLEAN_STATES:
            raise ValueError('Not a boolean: {}'.format(val))
        return CLIConfig._BOOLEAN_STATES[val.lower()]

    def set_value(self, section, option, value):
        if self.use_local_config:
            current_config_dir = os.path.join(os.getcwd(), os.path.basename(self.config_dir))
            config_file_path = os.path.join(current_config_dir, os.path.basename(self.config_path))
            if config_file_path == self._config_file_chain[0].config_path:
                self._config_file_chain[0].set_value(section, option, value)
            else:
                config = _ConfigFile(current_config_dir, config_file_path)
                config.set_value(section, option, value)
                self._config_file_chain.insert(0, config)
        else:
            self._config_file_chain[-1].set_value(section, option, value)

    def set_to_use_local_config(self, use_local_config):
        self.use_local_config = use_local_config


class _ConfigFile(object):
    _BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def __init__(self, config_dir, config_path):
        self.config_dir = config_dir
        self.config_path = config_path
        self.config_parser = get_config_parser()
        if os.path.exists(config_path):
            self.config_parser.read(config_path)

    def items(self, section):
        return self.config_parser.items(section) if self.config_parser else []

    def has_option(self, section, option):
        return self.config_parser.has_option(section, option) if self.config_parser else False

    def get(self, section, option):
        if self.config_parser:
            return self.config_parser.get(section, option)
        raise configparser.NoOptionError(section, option)

    def getint(self, section, option):
        return int(self.get(section, option))

    def getfloat(self, section, option):
        return float(self.get(section, option))

    def getboolean(self, section, option):
        val = str(self.get(section, option))
        if val.lower() not in _ConfigFile._BOOLEAN_STATES:
            raise ValueError('Not a boolean: {}'.format(val))
        return _ConfigFile._BOOLEAN_STATES[val.lower()]

    def set(self, config):
        ensure_dir(self.config_dir)
        with open(self.config_path, 'w') as configfile:
            config.write(configfile)
        os.chmod(self.config_path, stat.S_IRUSR | stat.S_IWUSR)
        self.config_parser.read(self.config_path)

    def set_value(self, section, option, value):
        config = get_config_parser()
        config.read(self.config_path)
        try:
            config.add_section(section)
        except configparser.DuplicateSectionError:
            pass
        config.set(section, option, value)
        self.set(config)
