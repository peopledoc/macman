#!/usr/bin/env python
"""Start, stop and manage virtual machines.

This is a wrapper around Vagrant.

"""
from contextlib import contextmanager
from optparse import OptionParser
import os
import subprocess
import sys

from vagrant_vm_manager import settings
from vagrant_vm_manager.templates import generate_vagrantfile


def main():
    """Parse shell args and execute action on VM."""
    # Parse shell argument
    try:
        config_filename = settings.find_config_file(os.getcwd())
    except settings.ConfigurationError:  # No file found.
        config_filename = os.path.join(os.path.abspath(os.getcwd()),
                                       'etc', 'vagrant_vm_manager.cfg')
        print "No configuration file found. Creating a new one at %s" \
              % config_filename
        if not os.path.exists(os.path.dirname(config_filename)):
            os.makedirs(os.path.dirname(config_filename))
        with open(config_filename, 'w') as config_file:
            vm_settings = settings.Settings()
            settings.write_config_file(vm_settings, config_file)
    vm_settings = settings.read_config_file(config_filename)
    vm_list = vm_settings.vms.keys()
    action_list = ['start', 'stop', 'download', 'configure', 'reconfigure',
                   'delete', 'ssh', 'restart', 'register', 'unregister',
                   'list']
    usage = """Usage: %%prog [options] ACTION VM.

Where:

* ACTION is one in (%s)
* VM is one in (all, %s)
    """ % (','.join(action_list), ', '.join(vm_list))
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args()

    try:
        action = args.pop(0)
    except IndexError:
        parser.error('Bad number of arguments. Missing ACTION.')

    try:
        vm = args.pop(0)
    except IndexError:
        vm = None
    if not action in action_list:
        parser.error('Unknow action %s' % action)
    if action == 'register':
        if not vm:
            parser.error('Bad number of arguments. Need a VM name.')
        if vm in vm_list:
            parser.error('VM %s already exists. Nothing done.' % vm)
        if vm is 'all':
            parser.error('"all" is not a valid VM name to register.')
        vm_settings.vms[vm] = {}
        with open(config_filename, 'w') as config_file:
            settings.write_config_file(vm_settings, config_file)
    elif action == 'unregister':
        if not vm:
            parser.error('Bad number of arguments. Need a VM name.')
        if vm not in vm_list:
            parser.error('VM %s does not exist. Nothing done.' % vm)
        if vm == 'all':
            vm_targets = vm_list
        else:
            vm_targets = [vm]
        for vm_name in vm_targets:
            del vm_settings.vms[vm_name]
        with open(config_filename, 'w') as config_file:
            settings.write_config_file(vm_settings, config_file)
    elif action == 'list':
        print "Registered virtual machines:"
        for vm_name in vm_list:
            print "* %s" % vm_name
    elif action == 'download':
        if vm and not vm in vm_list:
            vm_dir = os.path.join(settings.VM_DIR, vm)
            os.makedirs(vm_dir)
        manager = VMManager(vm)
        manager.download()
    else:
        if vm == 'all':
            vm_targets = vm_list
        else:
            if vm:
                if not vm in vm_list:
                    parser.error('Unknown VM %s' % vm)
                vm_targets = [vm]
            else:
                sys.stderr.write('Bad number of arguments. Need a VM name.\n')
                sys.exit(1)
        kwargs = {}
        if action == 'configure':
            for arg in args:
                parts = arg.partition('=')
                if not parts[0]:
                    parser.error('Bad argument %s. Missing assignation.' % arg)
                kwargs[parts[0]] = parts[2]
                vm_settings.vms[vm][parts[0]] = parts[2]
            with open(config_filename, 'w') as config_file:
                settings.write_config_file(vm_settings, config_file)
        for vm_name in vm_targets:
            print "On VM %s" % vm_name
            directory = os.path.join(vm_settings.directory, vm_name)
            manager = VMManager(vm_name, directory)
            manager.settings = vm_settings.default
            manager.settings.update(vm_settings.vms[vm_name])
            func = getattr(manager, action)
            func(**kwargs)


class VMManager(object):
    """Implementation of manager class for one VM."""
    def __init__(self, name, directory=''):
        self.name = name
        self.directory = directory
        #self.base_box = settings.get(self.name, 'base_box')

    def get_vm_dir(self):
        return self.directory

    def start(self):
        """Start VM by name."""
        if not self.is_configured():
            if not self.is_downloaded():
                self.download()
            self.configure()
        with chdir(self.get_vm_dir()):
            execute('vagrant up')

    def stop(self):
        """Stop VM by name."""
        with chdir(self.get_vm_dir()):
            execute('vagrant halt')

    def get_vagrantfile_path(self):
        return os.path.join(settings.VM_DIR, self.name, 'Vagrantfile')

    def is_configured(self):
        return os.path.exists(self.get_vagrantfile_path())

    def configure(self, **configuration):
        """Generate Vagrantfile for VM."""
        # Default generator. Could be configurable.
        generator = generate_vagrantfile
        # Default template source. Could be configurable.
        template = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'templates',
                                'Vagrantfile')
        # File output.
        vagrantfile = os.path.join(self.get_vm_dir(), 'Vagrantfile')
        # Context.
        context = configuration
        context.update(self.settings)
        context['box_name'] = self.name
        context['box_directory'] = self.get_vm_dir()
        generator(template, vagrantfile, context)

    def reconfigure(self):
        """Re-generate Vagrantfile for VM."""
        if settings.VM_RESET_VAGRANT_CMD:
            cmds = settings.VM_RESET_VAGRANT_CMD(self.name, self.base_box,
                                                 self.get_vagrantfile_path())
            for cmd in cmds:
                execute(cmd)
        else:
            self.configure()

    def is_downloaded(self):
        return os.path.exists(os.path.join(settings.VM_DIR, self.base_box))

    def download(self):
        """Download VM base box."""
        output_dir = settings.VM_DIR
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        execute('rsync --progress %s %s' % (settings.RSYNC_URL, output_dir))

    def delete(self):
        """Delete VM by name."""
        with chdir(self.get_vm_dir()):
            execute('vagrant destroy')
            execute('vagrant box remove %s' % self.name)

    def ssh(self):
        """SSH connect to the VM."""
        with chdir(self.get_vm_dir()):
            execute('vagrant ssh')

    def restart(self):
        """Restart the VM."""
        with chdir(self.get_vm_dir()):
            execute('vagrant reload')


def execute(command, data={}):
    """Execute a shell command.

    Command is a string ; data a dictionnary where values are supposed to be
    strings or integers and not variables or commands.

    Command and data are combined with string format operator.

    Return command's exit code.

    >>> execute_command('echo "%(msg)s"', {'msg': 'Hello world!'})
    Executing echo "Hello world!"
    0
    """
    if data:
        command = command % data
    print "Executing %s" % command
    return subprocess.call(command, shell=True)


@contextmanager
def chdir(path):
    previous_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(previous_dir)


if __name__ == '__main__':
    main()
