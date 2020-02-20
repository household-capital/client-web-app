# -*- mode: ruby -*-
# vi: set ft=ruby :
# please run:
# vagrant plugin install vagrant-hostmanager vagrant-cachier vagrant-vbguest vagrant-bindfs vagrant-env

# IP = "10.2.2.#{rand(02..254)}"

HOSTNAME = 'client-app.vm'

Vagrant.configure(2) do |config|
  config.env.enable
  config.hostmanager.enabled = true
  config.hostmanager.manage_host = true
  config.hostmanager.ignore_private_ip = false
  config.hostmanager.include_offline = true

  config.vm.define HOSTNAME do |node|
    node.vm.box      = 'ubuntu/bionic64'
    node.vm.hostname = HOSTNAME
    node.vm.host_name = HOSTNAME
    node.vm.synced_folder ".", "/vagrant", type: :nfs
    node.vm.network "private_network", ip: "10.2.2.123"
    node.vm.provision :shell, :inline => "echo \"Etc/UTC\" | sudo tee /etc/timezone && dpkg-reconfigure --frontend noninteractive tzdata"
  end

  config.vm.provider "virtualbox" do |v|
    v.gui = false
    v.name = HOSTNAME
    v.memory = 2048
    v.cpus = 2
  end

  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
    config.cache.synced_folder_opts = {
      # owner: "_apt",
      # group: "_apt"
      type: :nfs,
      mount_options: [
        'rw',
        'vers=3',
        'tcp',
        'nolock'
      ]
    }
  end

  config.vm.provision "shell", path: "provision_ubuntu.sh", privileged: false
end
