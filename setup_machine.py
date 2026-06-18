import ansible_runner
import subprocess
from uuid import uuid4

MACHINE_NAME_LIST = []

def extract_key_fields(raw_output: str):
    parsed = {}
    for line in raw_output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized_key = key.lower().strip()
        parsed[normalized_key] = value.strip()

    return parsed

username = input("Enter your username for the new user: ")
password = input("Enter your password for the new user: ")
ssh_port = input("Enter SSH port you want to use: ")
warp_type = input("Select warp type (1 for wgcf, 2 for official client): ")
xray_domain = input("Enter your domain for xray: ")

# Update apt package list and install necessary packages
r = ansible_runner.run(
    private_data_dir='.',
    playbook='software.yml',
    limit=",".join(MACHINE_NAME_LIST),
    tags="upgradepkg, addcommonpkg",
)

# setup new non-previliged user & ssh
r = ansible_runner.run(
    private_data_dir='.',
    playbook='createuser.yml',
    limit=",".join(MACHINE_NAME_LIST),
    extravars={
        "username": username,
        "password": password,
        "ssh_port": ssh_port
    },
)

# setup and enable ufw
ssh_port_rule = {
    "port": ssh_port,
    "proto": "tcp",
    "comment": "Allow SSH",
}
r = ansible_runner.run(
    private_data_dir='.',
    playbook='ufw.yml',
    limit=",".join(MACHINE_NAME_LIST),
    tags="ufwrule, enableufw",
    extravars={"rule": ssh_port_rule},
)

# enhance ssh security
r = ansible_runner.run(
    private_data_dir='.',
    playbook='ssh.yml',
    limit=",".join(MACHINE_NAME_LIST),
    extravars={"ssh_port": ssh_port},
)

# configure network
r = ansible_runner.run(
    private_data_dir='.',
    playbook='network.yml',
    limit=",".join(MACHINE_NAME_LIST),
    tags="bbr",
)

# setup warp
if warp_type == "1":
    r = ansible_runner.run(
        private_data_dir='.',
        playbook='software.yml',
        limit=",".join(MACHINE_NAME_LIST),
        tags="wgcf",
    )
else:
    r = ansible_runner.run(
        private_data_dir='.',
        playbook='software.yml',
        limit=",".join(MACHINE_NAME_LIST),
        tags="warp",
    )

# setup xray
key_result = subprocess.run(["xray", "x25519"], capture_output=True, text=True).stdout.strip()
key_fields = extract_key_fields(key_result)
xray_uuid = str(uuid4())

r = ansible_runner.run(
    private_data_dir='.',
    playbook='software.yml',
    limit=",".join(MACHINE_NAME_LIST),
    tags="xray",
    extravars={
        "uuid": xray_uuid,
        "domain": xray_domain,
        "privatekey": key_fields.get('privatekey'),
        "use_official_client": warp_type != "1"
    },
)

print("\nSetup completed! Here are information for connecting to xray:")
print(f"Masquerade domain: {xray_domain}")
print(f"UUID: {xray_uuid}")
print(f"PrivateKey: {key_fields.get('privatekey')}")
print(f"Password: {key_fields.get('password')}")
print(f"Hash32: {key_fields.get('hash32')}")
