#!/usr/bin/python
# -*- coding: utf-8 -*-
#License: Public Domain
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}
DOCUMENTATION = r'''
---
module: get_version
short_description: Windows get OS verison and return changed flag if below min
description:
  - Checks Windows OS version and returns the version data in JSON
  - Checks that the min version against the passed "major,minor,build" parameters
  - Returns "changed" if the remote system's OS version is below a minimum
  - The "changed" flag is t notify operations or to trigger another task
options:
  major:
    description:
      - Windows major version [MAJOR.minor.build]
    default: 5
  minor:
    description:
      - Windows minor version [major.MINOR.build]
    default: 1
  build:
    description:
      - Windows build version [major.minor.BUILD]
    default: None
author:
- Robert Keith (Argon Systems)
'''

EXAMPLES = r'''
# Example Ansible Playbook
- name: test remote Windows OS version
  hosts: windows
  tasks:
    - name: PowerShell module example to get Windows OS version
      get_version:
        major: "5"
        minor: "1"
        build: "13493"

'''

RETURN = '''
    description: Output of (Get-Host).Version powershell in JSON format
    returned: success
    type: string
'''
