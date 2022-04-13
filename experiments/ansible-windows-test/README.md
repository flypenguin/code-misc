# Ansible Windows Readme


## Ansible config

- Ansible machine
  - Install `pywinrm`
  - Mac only
    - `export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` before running Ansible
      - https://github.com/ansible/ansible/issues/32499#issuecomment-341578864
    - Kerberos does not seem to work
- Windows machine
  - [Execute this](https://docs.ansible.com/ansible/2.5/user_guide/windows_setup.html#winrm-setup)
  - Create `Ansible` user, needs `logon` rights.

Test command: `ansible win0 -m win_shell -a 'Get-CimInstance -ClassName win32_operatingsystem | select csname, lastbootuptime'`


### Generic Windows "Ansible" links

- (!!) https://www.ansible.com/blog/windows-updates-and-ansible
- (!!) https://4sysops.com/archives/automate-windows-updates-with-ansible/
- https://pablodav.github.io/post/ansible_win/ansible_win_updates_patch_security/

## Example windows server 1

Domain Services installed. Other settings below.

- Domain: `roggy.local`
- `secpol.msc`: disabled password complexity requirements
- Passwords
  - Administrator: `Administrator1`
  - Directory Services Restore Mode (DSRM) password: `Directory1`
- NetBIOS name: `ROGGY`
- Windows folders
  - Database folder: `C:\Windows\NTDS`
  - Log files folder: `C:\Windows\NTDS`
  - SYSVOL folder: `C:\Windows\SYSVOL`
