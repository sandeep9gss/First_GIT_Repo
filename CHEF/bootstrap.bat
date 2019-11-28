
call winrm quickconfig -q
call sc config mpssvc start= demand
call sc start mpssvc
call winrm get winrm/config
call winrm set winrm/config @{MaxTimeoutms="1800000"}
call winrm set winrm/config/service @{AllowUnencrypted="true"}
call winrm set winrm/config/service/auth @{Basic="true"}
call winrm set winrm/config/client/auth @{Basic="true"}
call winrm set winrm/config/service/auth @{CredSSP="True"}
call winrm set winrm/config/winrs @{MaxMemoryPerShellMB="4096"}
call winrm set winrm/config/client @{TrustedHosts="*"}
call winrm set winrm/config/winrs @{AllowRemoteShellAccess="True"}
call netsh advfirewall firewall add rule name="WinRM 5985" protocol=TCP dir=in localport=5985 action=allow
call netsh advfirewall firewall add rule name="WinRM 5986" protocol=TCP dir=in localport=5986 action=allow
call net stop winrm
call sc config winrm start= auto
call net start winrm
