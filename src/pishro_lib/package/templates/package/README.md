# Pishro {{ package_name }} Package

This is a Pishro package that installs and manages **{{ package_name }}** in a Docker Swarm environment.

## Requirements
- Pishro cli is installed.
- Docker Engine with Swarm mode enabled.
- Basic knowledge of Docker and {{ package_name }} configuration.

## Installation
Add the pishro-catalog:

```bash
uv run pishro repo add --url https://github.com/siavashoutadi/pishro-catalog.git pishro-catalog
```

Download the {{ package_name }} package:

```bash
pishro package download --repo pishro-catalog --name {{ package_name }} --destination ./pishro-packages
```

Add custom values:

```bash
editor values.yaml
```

Override the values according to the requirements by adding the following lines to the `values.yaml` file. For example:

```yaml
deploy:
  resources:
    limits:
      cpu: "2"
      memory: "2G"
    requests:
      cpu: "1"
      memory: "1G"
  mode: replicated
  replicas: 3

networks:
  - my_network
```

Install the package:

```bash
uv run pishro package install --packages-path ./pishro-packages/ --name {{ package_name }} --override-values-file ./values.yaml
```
