from ConfigParser import ConfigParser
from os import getcwd
from os.path import abspath, dirname, join, isfile


def is_root_path(path):
    """Return True if path has no parent."""
    return dirname(path) is path


class ConfigurationError(Exception):
    """To be raised on configuration problem."""


def find_config_file(origin_path):
    """Return first config file found in origin path or ascendant folders.

    The following patterns return positive match, in order:

    * "macman.cfg" in ``origin_path``
    * "etc/macman.cfg" in ``origin_path``
    * patterns above in ``origin_path``'s parent folder, recursively. It means
      it could fallback to "/etc/macman.cfg"

    Raises ConfigurationError is no file is found.

    """
    if isfile(origin_path):
        origin_path = dirname(origin_path)
    origin_path = abspath(origin_path)
    patterns = ['macman.cfg',
                join('etc', 'macman.cfg')]
    for pattern in patterns:
        config_file = join(origin_path, pattern)
        if isfile(config_file):
            return config_file
    if is_root_path(origin_path):
        raise ConfigurationError('No configuration file found.')
    return find_config_file(dirname(origin_path))


def read_config_file(filename):
    """Return Settings instance built from contents of ``filename`` file."""
    parser = ConfigParser()
    parser.read(filename)
    settings = Settings()
    core_section = 'macman'
    default_section = 'default'
    # Handle core configuration.
    if parser.has_section(core_section):
        section = core_section
        for option in ['directory']:
            if parser.has_option(section, option):
                setattr(settings, option, parser.get(section, option))
    # Handle default configuration.
    if parser.has_section(default_section):
        section = settings.default
        settings.default = dict(parser.items(section))
    # Handle configuration of VMs.
    special_sections = (core_section, default_section)
    for section in parser.sections():
        if section in special_sections:
            continue
        vm_id = section
        settings.vms[vm_id] = dict(parser.items(section))
    return settings


def write_config_file(settings, file_obj):
    """Save settings into file."""
    default_settings = Settings()
    parser = ConfigParser()
    core_section = 'macman'
    default_section = 'default'
    # Internal options.
    # Order internal options alphabetically so that output is repeatable and
    # predictable.
    core_options = []
    for option in ['directory']:
        value = getattr(settings, option)
        is_default = False
        try:
            default_value = getattr(default_settings, option)
        except AttributeError:
            pass
        else:
            if default_value == value:
                is_default = True
        if not is_default:
            core_options.append(option, value)
    if core_options:
        parser.add_section(core_section)
        for option, value in core_options:
            parser.set(core_section, option, value)
    # Default options.
    default_options = []
    options = settings.default.keys()
    options.sort()
    for option in options:
        value = settings.default[option]
        is_default = False
        try:
            default_value = default_settings.default[option]
        except KeyError:
            pass
        else:
            if default_value == value:
                is_default = True
        if not is_default:
            default_options.append(option, value)
    if default_options:
        parser.add_section(default_section)
        for option, value in default_options:
            parser.set(default_section, option, value)
    # VM options.
    vm_ids = settings.vms.keys()
    vm_ids.sort()
    for vm in vm_ids:
        parser.add_section(vm)
        options = settings.vms[vm].keys()
        options.sort()
        for option in options:
            parser.set(vm, option, settings.vms[vm][option])
    # Write the file.
    parser.write(file_obj)


class Settings(object):
    """VM manager settings container."""
    def __init__(self):
        self.vms = {}
        """Virtual machines key-value store.

        Keys are VM identifiers.
        Values are dictionaries containing VM configuration.

        """

        self.default = {
            'cpus': 1,
            'ram': 512,
            'vram': '16',
            'ip': '34.34.34.10',
            'url': 'http://files.vagrantup.com/lucid64.box',
            'boot_mode': 'headless',
            'ssh_forward_agent': 'true',
        }
        """Default options for VMs."""

        self.directory = join(abspath(getcwd()), 'var', 'vm')
        """Path to directory where to store VMs (i.e. Vagrantfiles)."""

    def get(self, vm, option):
        """Return option value for VM, with fallback to default values."""
        return self.vms[vm].get(option, self.default.get(option))
