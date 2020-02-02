#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# dehydrated-hook-fortigate - Certificate Deploy Script for dehydrated
#
# This script deploys certificates to a Fortigate firewall and can set
# the certificate as the admin, vpn, and/or wifi certificate.
# 
#
# Copyright (C) 2020 Joshua Nord <joshua@thenords.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
################################################################################

import os
import sys
import re
import configparser
from pexpect import pxssh
from OpenSSL import crypto

encoding = 'utf-8'
defaults = {
    "configfiles": [
        "/etc/dehydrated/dehydrated-hook-fortigate.conf",
        "/usr/local/etc/dehydrated/dehydrated-hook-fortigate.conf",
        "%s/dehydrated-hook-fortigate.conf" % os.getenv("BASEDIR"),
        "dehydrated-hook-fortigate.conf", ]
}

def deploy(domain, keyfile, certfile):
   
    cfgfiles = defaults["configfiles"]

    config = configparser.ConfigParser()
    config.read(cfgfiles)

    if (config.has_section(domain)):
        print(f"deploying certificate for {domain}")

        cert_data = open(certfile).read()
        key_data = open(keyfile).read()

        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)
        
        cert_name = "LE_%s_%s" % (domain.partition(".")[0], cert.get_notBefore().decode(encoding))

        print(f"cert_name = {cert_name}")

        host = config.get(domain, "host")
        port = config.get(domain, "sshport")
        username = config.get(domain, "username")
        password = config.get(domain, "password")
 
        set_vpn = config.getboolean(domain, "vpn")
        set_wifi = config.getboolean(domain, "wifi")
        set_admin = config.getboolean(domain, "admin")

        expect_session = pxssh.pxssh(timeout=5,encoding=encoding)

        # custom prompt for Fortigate
        expect_session.PROMPT = r"\r\n[^\r\n ]+( \(local\))? [#$] "
        
        print(f"connecting to {host} on port {port} with username {username}")

        expect_session.login(host,username,password,port=port,auto_prompt_reset=False,original_prompt=expect_session.PROMPT,sync_original_prompt=False)

        print("session logged in ")

        expect_session.sendline('config vpn certificate local')
        expect_session.prompt()
        
        expect_session.sendline('get')
        existing_certs = ""
        i = 1
        while i == 1:
            i = expect_session.expect([expect_session.PROMPT, "--More--"])
            if (i == 1):
                existing_certs += expect_session.before
                expect_session.sendline()

        existing_certs += expect_session.before

        r = re.compile(r"name: ([^ ]+)")
        existing_certs = list(filter(lambda l: r.match(l), existing_certs.splitlines()))
        existing_certs = list(map(lambda l: r.search(l).group(1), existing_certs))
        print("Found %d certs: %s" % (len(existing_certs), existing_certs))

        installed = False

        if cert_name in existing_certs:
            print(f"Certificate {cert_name} already installed.")
        else:
            print(f"Installing certificate {cert_name}")
 
            expect_session.sendline(f"edit {cert_name}")
            expect_session.prompt()

            #print(f"set private-key \"{key_data}\"")
            expect_session.sendline(f"set private-key \"{key_data}\"")
            expect_session.prompt()

            #print(f"set certificate \"{cert_data}\"")
            expect_session.sendline(f"set certificate \"{cert_data}\"")
            expect_session.prompt()

            installed = True

        expect_session.sendline('end')
        expect_session.prompt()

        if installed:
            if set_wifi:
                print(f"Setting wifi cert to {cert_name}")
                expect_session.sendline(f"config system global")
                expect_session.prompt()

                expect_session.sendline(f"set wifi-certificate {cert_name}")
                expect_session.prompt()

                expect_session.sendline(f"end")
                expect_session.prompt()

            if set_vpn:
                print(f"Setting sslvpn cert to {cert_name}")
                expect_session.sendline(f"config vpn ssl settings")
                expect_session.prompt()

                expect_session.sendline(f"set servercert {cert_name}")
                expect_session.prompt()

                expect_session.sendline(f"end")
                expect_session.prompt()

            if set_admin:
                print(f"Setting admin cert to {cert_name}")
                expect_session.sendline(f"config system global")
                expect_session.prompt()

                expect_session.sendline(f"unset admin-server-cert")
                expect_session.prompt()

                expect_session.sendline(f"end")
                expect_session.prompt()

                expect_session.sendline(f"config system global")
                expect_session.prompt()

                expect_session.sendline(f"set admin-server-cert {cert_name}")
                expect_session.prompt()

                expect_session.sendline(f"end")
                expect_session.prompt()

        expect_session.logout() 

        print(f"Finished deploy for {domain}")

    else:
        print(f"no fortigate config found for {domain}")

def unchanged_cert(domain, keyfile, certfile):
    print("unchanged_cert method")
    deploy(domain, keyfile, certfile);

def deploy_cert(domain, keyfile, certfile):
    print("deploy_cert method")
    deploy(domain, keyfile, certfile);

def main(handler, args):

    domain = ""
    keyfile = ""
    certfile = ""
    fullchainfile = ""
    chainfile = ""

    if (len(args) >= 5):
        domain = args[0]
        keyfile = args[1]
        certfile = args[2]
        fullchainfile = args[3]
        chainfile = args[4]

    handlers = {
        "unchanged_cert": unchanged_cert,
        "deploy_cert": deploy_cert
    }

    h = handlers.get(handler);
    if (h):
        h(domain, keyfile, certfile)


if __name__=='__main__':
    try:
        handler = sys.argv[1]
        args = sys.argv[2:]

    except IndexError:
        print("Missing required handler parameter")
        sys.exit(1)

    main(handler, args)
