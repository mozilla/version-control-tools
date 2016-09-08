# -*- mode: ruby -*-
# vi: set ft=ruby :

# NOTE: This script requires the Nugrant Vagrant plugin:
# https://github.com/maoueh/nugrant
#
# You can install it with:
#
#   $ vagrant plugin install nugrant
#
# You can override this Vagrantfile's settings using your own .vagrantuser
# file.  See https://github.com/maoueh/nugrant/blob/master/README.md
# for details.

unless Vagrant.has_plugin?("nugrant")
  raise 'nugrant plugin is not installed.  Please read this Vagrantfile for instructions on installing it.'
end

Vagrant.configure(2) do |config|

  # Default guest settings.  You can override these in your .vagrantuser
  # file.  See the '.vagrantuser.example' file in the project root for some
  # common values for these settings.
  config.user.defaults = {
    "private_ip" => "192.168.33.33",
    "cpus" => "2",
    "memory" => "2048",
    "show_gui" => false,
    "synced_folder" => ".",
    "playbook" => "testing/vagrant/configure.yml",
    "ansible_verbose" => "",
    "ansible_args" => []
  }

  # We use the opscode bento project's boxes because they come with 40Gb
  # disks. Many other official distro images only come with 10Gb disks.
  # https://github.com/chef/bento
  config.vm.box = "bento/centos-7.2"

  # We need to bind to the default /vagrant directory so the ansible_local
  # provisioner knows where to find our playbooks.
  config.vm.synced_folder config.user.synced_folder, "/vagrant"
  config.vm.synced_folder config.user.synced_folder, "/home/vagrant/vct"

  # FIXME: This affects Vagrant 1.8.5.  We can remove it with Vagrant 1.8.6.
  # Use the default key, already part of the bento box build, to prevent
  # SSH auth errors during 'vagrant up' using the vmware_workstation provider.
  # See https://github.com/mitchellh/vagrant/issues/7610
  config.ssh.insert_key = false

  config.vm.network "private_network", ip: config.user.private_ip

  config.vm.provider "vmware_fusion" do |v|
    v.gui = config.user.show_gui
    v.vmx["memsize"] = config.user.memory
    v.vmx["numvcpus"] = config.user.cpus
  end

  config.vm.provider "vmware_workstation" do |v|
    v.gui = config.user.show_gui
    v.vmx["memsize"] = config.user.memory
    v.vmx["numvcpus"] = config.user.cpus
  end

  config.vm.provider "virtualbox" do |vb|
    vb.gui = config.user.show_gui
    vb.memory = config.user.memory
    vb.cpus = config.user.cpus
  end

  # Re-run after dev environment configuration changes with 'vagrant provision'
  config.vm.provision "ansible_local" do |ansible|

    # Ansible needs to know the private_ip that the guest and host are using
    # so that it can correctly set up the mozreview services.  We'll pass it in
    # as an extra variable.
    ansible.extra_vars = {
      docker_listen_ip: config.user.private_ip
    }

    ansible.verbose = config.user.ansible_verbose
    ansible.playbook = config.user.playbook
    ansible.raw_arguments = config.user.ansible_args
  end
end
