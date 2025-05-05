# Pishro

Pishro is a package manager and deployment tool for Docker Swarm that simplifies application deployment and management in containerized environments.

## Overview

Pishro provides a streamlined workflow for packaging, distributing, and deploying applications to Docker Swarm clusters. It handles the complexities of container orchestration, allowing developers and operations teams to focus on their applications rather than infrastructure details.

## Features

- **Package Management**: Create, version, and distribute application packages
- **Git Integration**: Pull application code directly from Git repositories
- **Docker Swarm Deployment**: Simplified deployment to Docker Swarm clusters
- **Template-based Configuration**: Use Jinja2 templates for flexible configuration
- **Application Lifecycle Management**: Tools for installing, updating, and removing applications

## Installation

```bash
pip install pishro-lib
```

## Requirements

- Python 3.13 or higher
- Docker
- Docker Swarm cluster (for deployment)

## Usage

Detailed usage instructions and examples coming soon.

## Development

### Setting up the development environment

```bash
# Clone the repository
git clone https://github.com/yourusername/pishro.git
cd pishro

# Install development dependencies
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

## License

See the [LICENSE](LICENSE) file for details.
