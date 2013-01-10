#!/usr/bin/env python
"""Start, stop and manage virtual machines for PostBox's DEV environment.

This is a wrapper around Vagrant.

"""
from contextlib import contextmanager
from optparse import OptionParser
import os
import subprocess
import sys

import settings


def get_vm_list():
    """Scan filesystem and return list of available VMs."""
    vm_list = []
    vm_dir = settings.VM_DIR
    if os.path.isdir(vm_dir):
        items = os.listdir(vm_dir)
        vm_list = [os.path.basename(item) for item in items
                   if os.path.isdir(os.path.join(vm_dir, item))]
    return vm_list


def main():
    """Parse shell args and execute action on VM."""
    # Parse shell argument
    vm_list = get_vm_list()
    action_list = ['start', 'stop', 'download', 'configure', 'reconfigure',
                   'delete', 'ssh', 'restart']
    usage = """Usage: %%prog [options] ACTION VM.

Where:

* ACTION is one in (%s)
* VM is one in (all, %s)
    """ % (','.join(action_list), ','.join(vm_list))
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args()
    if len(args) > 2 or len(args) < 1:
        parser.error('Bad number of arguments.')

    action = args[0]

    try:
        vm = args[1]
    except IndexError:
        vm = None
    if not action in action_list:
        parser.error('Unknow action %s' % action)
    if action != 'download':
        if vm == 'all':
            vm_targets = vm_list
        else:
            if vm:
                vm_targets = [vm]
            else:
                sys.stderr.write('Bad number of arguments. Need a VM name.\n')
                sys.exit(1)
        for vm_name in vm_targets:
            print "On VM %s" % vm_name
            manager = VMManager(vm_name)
            func = getattr(manager, action)
            func()
    else:
        if vm and not vm in vm_list:
            vm_dir = os.path.join(settings.VM_DIR, vm)
            os.makedirs(vm_dir)
        manager = VMManager(vm)
        manager.download()


class VMManager(object):
    def __init__(self, name):
        self.name = name
        self.base_box = settings.VM_BASE_BOX

    def get_vm_dir(self):
        return os.path.join(settings.VM_DIR, self.name)

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

    def configure(self):
        """Generate Vagrantfile for VM."""
        if settings.VM_CREATE_VAGRANT_CMD:
            cmds = settings.VM_CREATE_VAGRANT_CMD(self.name, self.base_box,
                                                  self.get_vagrantfile_path())
            for cmd in cmds:
                execute(cmd)
        else:
            raise NotImplementedError('You must create your Vagrantfile')

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