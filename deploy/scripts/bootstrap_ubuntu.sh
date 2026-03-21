#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
SUDO=""

if [ "${EUID}" -ne 0 ]; then
  SUDO="sudo"
fi

$SUDO apt update
$SUDO apt upgrade -y
$SUDO apt install -y ca-certificates curl git gnupg lsb-release

for package in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
  $SUDO apt remove -y "$package" >/dev/null 2>&1 || true
done

$SUDO install -m 0755 -d /etc/apt/keyrings
$SUDO curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
$SUDO chmod a+r /etc/apt/keyrings/docker.asc

$SUDO tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF

$SUDO apt update
$SUDO apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
$SUDO systemctl enable docker
$SUDO systemctl restart docker
$SUDO usermod -aG docker "$USER"

echo
echo "Bootstrap complete."
echo "Recommended next steps:"
echo "1. Log out and log back in so the docker group membership takes effect."
echo "2. Ensure Tencent Cloud security group inbound rules allow TCP 22 and TCP 80."
echo "3. Clone the project into /opt/mall."
