# Security Review

The Security stage in Jenkins uses Bandit and Trivy to check the application for security problems.

## Bandit

Bandit is used to scan the Python code.

In the latest scan, Bandit did not find any security issues in `app.py`.

## Trivy

Trivy is used to scan the Docker image and check the installed system and Python packages for known vulnerabilities.

The pipeline is set to stop if Trivy finds a fixable CRITICAL vulnerability.

In the latest scan, Trivy found:

- 0 CRITICAL vulnerabilities
- 44 HIGH vulnerabilities in Debian packages
- 4 HIGH vulnerabilities in Python package information

The Debian vulnerabilities are mainly from packages that come with the Python Debian base image. The Dockerfile already runs `apt-get update` and `apt-get upgrade` during the build so available system updates are installed.

The Docker build also upgrades pip and setuptools before installing the project requirements.

Some HIGH vulnerabilities are still reported because they are part of the base image or do not currently have a fix available. These issues are still shown in the Jenkins output so they can be checked again in future builds.

The pipeline will stop if a fixable CRITICAL vulnerability is found. HIGH vulnerabilities are reported so they can be reviewed instead of being ignored.