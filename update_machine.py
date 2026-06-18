import ansible_runner

MACHINE_NAME_LIST = []

# update packages
r = ansible_runner.run(
    private_data_dir='.',
    playbook='software.yml',
    tags="upgradepkg, autoremove",
    limit=",".join(MACHINE_NAME_LIST),
)

# reboot machines
r = ansible_runner.run(
    private_data_dir='.',
    playbook='common.yml',
    tags="reboot",
    limit=",".join(MACHINE_NAME_LIST),
)
