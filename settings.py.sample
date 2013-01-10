import os

ROOT_DIR = os.path.abspath(os.getcwd())
VM_DIR = os.path.join(ROOT_DIR, 'var', 'vm')

VM_BASE_BOX = 'vagrant-debian-6.0.5-amd64.box'
RSYNC_URL = 'user@host:path/%s' % VM_BASE_BOX


# Shell command that will be executed to create the Vagrantfile
def VM_CREATE_VAGRANT_CMD(box_name, base_box, vagrant_path):
    try:
        os.makedirs(os.path.dirname(vagrant_path))
    except OSError as e:
        print e.message
    return ["""cat > %(vagrant_path)s <<EOF
# -*- mode: ruby -*-
# Generated with vm
# **YOU SHOULD NOT EDIT THIS FILE MANUALLY.**
# You had better edit templates and presets, then run the generator again.
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  # All Vagrant configuration is done here. The most common configuration
  # options are documented and commented below. For a complete reference,
  # please see the online documentation at vagrantup.com.

  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "%(box_name)s"

  # The url from where the 'config.vm.box' box will be fetched if it
  # doesn't already exist on the user's system.
  config.vm.box_url = "%(base_box)s"

  # Boot with a GUI so you can see the screen. (Default is headless)
  config.vm.boot_mode = :gui

  # Assign this VM to a host-only network IP, allowing you to access it
  # via the IP. Host-only networks can talk to the host machine as well as
  # any other machines on the same network, but cannot be accessed (through
  # this network interface) by any external networks.
  config.vm.network :hostonly, "34.34.34.10"

  # Assign this VM to a bridged network, allowing you to connect directly to a
  # network using the host's network device. This makes the VM appear as
  # another physical device on your network.
  # config.vm.network :bridged

  # Forward a port from the guest to the host, which allows for outside
  # computers to access the VM, whereas host only networking does not.
  # config.vm.forward_port 80, 8080

  # VM hardware configuration.
  config.vm.customize ["modifyvm", :id, "--memory", 512]
  config.vm.customize ["modifyvm", :id, "--cpus", 1]
  config.vm.customize ["modifyvm", :id, "--vram", 16]

end
EOF""" % {'box_name': box_name,
          'base_box': base_box,
          'vagrant_path': vagrant_path}]

# Shell command that will be executed to reset the Vagrantfile, fall
# back to creation command
VM_RESET_VAGRANT_CMD = None
