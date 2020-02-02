# dehydrated-hook-fortigate
Python hook for the [dehydrated](https://github.com/dehydrated-io/dehydrated) project to install certificates obtained from Let's Encrypt/ACME on a Fortigate firewall.

When configured as a hook for the dehydrated script, this script will connect to a Fortigate firewall via SSH, check whether the latest certificate is already installed, install the certificate if not, and optionally configure the certificate as the admin, VPN, and/or wifi certificate on the device.


## Required Python Libraries
* [pexpect](https://github.com/pexpect/pexpect) - a Pure Python Expect-like module
* [pyopenssl](https://www.pyopenssl.org/) - a rather thin wrapper around (a subset of) the OpenSSL library


## Configuration
The script reads a configuration file from these default locations:
- `$(pwd)/dehydrated-hook-fortigate.conf`
- `$(BASEDIR)/dehydrated-hook-fortigate.conf`
- `/etc/dehydrate/dehydrated-hook-fortigate.conf`
- `/usr/local/etc/dehydrate/dehydrated-hook-fortigate.conf`

The configuration file uses a simple `INI`-style syntax, where you can set the parameters for each domain separately (by creating a section named after the domain).

The following parameters can be set:
- `host` the DNS hostname or IP address of the Fortigate firewall (**required**)
- `sshport` the SSH port to connect to on the Fortigate fireall host (default: *22*)
- `username` the username authorized to connect to the Fortigate fireall host **required**)
- `password` the password for the username authorized to connect to the Fortigate fireall host **required**)
- `admin` indicates whether the certificate should be configured as the Fortigate admin certificate (default: *False*)
- `wifi` indicates whether the certificate should be configured as the Fortigate WiFi certificate (default: *False*)
- `vpn` indicates whether the certificate should be configured as the Fortigate VPN certificate (default: *False*)

An example can be found in the `dehydrated-hook-fortigate.conf` file.


## Usage
Include this script as part of the hook chain in your [dehydrated](https://github.com/dehydrated-io/dehydrated) configuration.
 

```
$ ./dehydrated --hook ./hooks/fortigate/dehydrated-hook-ddns-fortigate.py
```

## Contribute
Please open an issue or submit a pull request.