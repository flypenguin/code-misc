# Ansible Windows Readme

## TL;DR - demo commands

```bash
# install some software
ansible-playbook playbooks/install-7zip-msi.yaml -l win1
ansible-playbook playbooks/install-notepadplusplus-choco.yaml -l win-srv

# demo a powershell module
ansible-playbook playbooks/test-powershell-module.yaml

# update things - the piece de resistance :)
ansible-playbook playbooks/update-cascaded-reboot.yaml       # for all hosts
```

## Ansible config

- Ansible machine
  - Install `pywinrm`
  - Mac only
    - `export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` before running Ansible
      - https://github.com/ansible/ansible/issues/32499#issuecomment-341578864
    - Kerberos does not seem to work
- Windows machine
  - Create an `Ansible` user, needs admin-rights and logon privileges
  - Enable Remote Desktop Access as described [here](https://www.rootusers.com/how-to-enable-remote-desktop-in-windows-server-2019/)
  - [Do this](https://docs.ansible.com/ansible/2.5/user_guide/windows_setup.html#winrm-setup) OR copy-paste below script to powershell (it's the same)
    ```powershell
    $url = "https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/ConfigureRemotingForAnsible.ps1"
    $file = "$env:temp\ConfigureRemotingForAnsible.ps1"
    (New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
    powershell.exe -ExecutionPolicy ByPass -File $file
    ```
  - Create `Ansible` user, needs `logon` rights.

Test commands:

- `ansible win_servers -m win_ping`
- `ansible win_servers -m win_shell -a 'Get-CimInstance -ClassName win32_operatingsystem | select csname, lastbootuptime'`

**NOTE:** Did not get Ansible-login working on the AD machine using _only_ GPOs. I had to add the Ansible user to the `Administrators` group manually.

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
  - Ansible: `Ansible1`
  - Directory Services Restore Mode (DSRM) password: `Directory1`
- NetBIOS name: `ROGGY`
- Windows folders
  - Database folder: `C:\Windows\NTDS`
  - Log files folder: `C:\Windows\NTDS`
  - SYSVOL folder: `C:\Windows\SYSVOL`

# Links

- https://www.jonathanmedd.net/2019/09/ansible-windows-and-powershell-the-basics-introduction.html
- https://github.com/PacktPublishing/Ansible-Quick-Start-Guide/blob/master/Chapter04/Ansible_Windows_Modules/Readme.md
- https://argonsys.com/microsoft-cloud/articles/configuring-ansible-manage-windows-servers-step-step/

Specific for Windows updates:

- https://www.catalog.update.microsoft.com/Search.aspx?q=Server+2019
- https://www.lagerhaus128.ch/?p=941
- https://4sysops.com/archives/automate-windows-updates-with-ansible/
- https://www.ansible.com/blog/windows-updates-and-ansible
- https://aptic.ch/ein-problem-weniger-vollautomatisches-windows-server-patching-mit-ansible/
- https://docs.ansible.com/ansible/latest/collections/community/windows/win_hotfix_module.html
- https://www.bleepingcomputer.com/news/microsoft/how-to-get-a-list-of-installed-windows-10-updates/
-
VMware:

- https://docs.ansible.com/ansible/latest/collections/community/vmware/index.html
