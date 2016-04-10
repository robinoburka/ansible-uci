#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Robin Obůrka <r.oburka@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: uci
author: "Robin Obůrka, @robinoburka"
short_description: Manipulates with UCI configuration files
description:
    - Manipulates with UCI configuration files on OpenWrt operating system.
version_added: "1.1"
options:
    name:
        description:
            - name of option to set/delete
        required: false
        aliases: key
    value:
        description:
            - value of changed option
        required: false
        aliases: val
    package:
        description:
            - package where is the section located
        required: true
        aliases: p
    section:
        description:
            - name of manipulated section
        required: false
        aliases: s
    type:
        description:
            - type of section - necessary information for non-existing sections
        required: false
    index:
        description:
            - index of anonymous section
            - defaults to 0 so the unique section is possible to access only trough its type
        required: false
        default: 0
    item:
        description:
            - value is option/list
        choices: [ 'option', 'list' ]
        required: false
        default: option
    state:
        description:
            - state of the section/option
        choices: [ 'present', 'absent' ]
        required: false
        default: present
    create:
        description:
            - enable or disable creating of non-existing sections/options
        choices: [ 'yes', 'no' ]
        required: false
        default: yes
notes:  []
'''
EXAMPLES = '''
# Set option in named section dhcp.lan.start to 100
- uci: p=dhcp s=lan name=start val=100

# Set option (and create if not exists) in named section of type host dhcp.computer.ip
- uci: p=dhcp s=computer type=host name=ip val=1.0.0.0

# Delete option in named section dhcp.computer.ip (doesn't delete empty section)
- uci: p=dhcp s=computer name=ip val=1.0.0.0 state=absent

# Create new named section of type host
- uci: p=dhcp s=computer2 type=host

# Delete whole named section
- uci: p=dhcp s=computer2 state=absent

# Please note that using anonymous section with Ansible is not good idea.
# The unique anonymous sections (always with index 0) are to only reasonable exception

# Set option in unique anonymous section of type dnsmasq dhcp.@dnsmasq[0].domain to example.com
- uci: p=dhcp type=dnsmasq name=domain val=example.com

# ... or specify the index explicitly
- uci: p=dhcp type=dnsmasq index=0 name=domain val=example.com
'''


def val_or_none(params, key):
    if key not in params:
        return None

    return params[key]


def get_uci_key(module, package, section, type, index, name):
    if section:
        if name:
            key = "{}.{}.{}".format(package, section, name)
        else:
            key = None
        skey = "{}.{}".format(package, section)
        return key, skey

    elif type and index:
        if name:
            key = "{}.@{}[{}].{}".format(package, type, index, name)
        else:
            key = None
        skey = "{}.@{}[{}]".format(package, type, index)
        return key, skey

    else:
        module.fail_json(msg="Definition of the key is ambiguous.")


def split_key(key):
    parts = key.split(".")
    if len(parts) == 2:
        return parts[0], parts[1]
    elif len(parts) == 3:
        return parts[0], parts[1], parts[2]


def is_set(item, val, expected=None):
    if not expected:
        return val
    else:
        if item == "option":
            return expected == val
        else:
            if val.find(expected) == -1:
                return False
            else:
                return True


def uci_commit(module, binary, package):
    status, stdout, stderr = module.run_command("{} commit {}".format(binary, package))
    if status != 0:
        module.fail_json(msg="Commit failed with: {}".format(stderr))


def uci_delete(module, binary, item, key, val=None):
    if item == "list" and not val:
        module.fail_json(msg="Delete of list's item requested but no value specified")

    if item == "option":
        status, stdout, stderr = module.run_command("{} delete {}".format(binary, key))
    else:
        status, stdout, stderr = module.run_command("{} del_list {}={}".format(binary, key, val))

    if status != 0:
        module.fail_json(msg="Command uci failed with: {}".format(stderr))

    uci_commit(module, binary, split_key(key)[0])
    module.exit_json(changed=True)


def uci_get(module, binary, key):
    status, stdout, stderr = module.run_command("{} get {}".format(binary, key))

    if status == 0:
        return stdout.strip()

    else:
        if stderr.find("Entry not found") == -1:
            module.fail_json(msg="Command uci failed with: {}".format(stderr))

        else:
            return None


def uci_set(module, binary, item, key, value, noreturn=False):
    if not value:
        module.fail_json(msg="Value wasn't provided")

    cmd = "set" if item == "option" else "add_list"

    status, stdout, stderr = module.run_command("{} {} {}='{}'".format(binary, cmd, key, value))
    if status != 0:
        module.fail_json(msg="Command uci failed with: {}".format(stderr))

    if not noreturn:
        uci_commit(module, binary, split_key(key)[0])
        module.exit_json(changed=True)


def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(aliases=["key"], required=False),
            value = dict(aliases=["val"], required=False),
            package = dict(aliases=["p"], required=True),
            section = dict(aliases=["s"], required=False),
            type = dict(required=False),
            index = dict(default="0", required=False),
            item  = dict(default="option", choices=["option", "list"]),
            state  = dict(default="present", choices=["present", "absent"]),
            create = dict(default="yes", type='bool')
        )
    )

    bin_path = module.get_bin_path('uci', True, ['/sbin', '/bin'])

    if not bin_path:
        module.fail_json(msg="Binary 'uci' not found.")

    p = module.params

    ## Receive values for better manipulation
    name = val_or_none(p, "name")
    value = val_or_none(p, "value")
    package = val_or_none(p, "package")
    section = val_or_none(p, "section")
    type = val_or_none(p, "type")
    index = val_or_none(p, "index")
    item = val_or_none(p, "item")
    state = val_or_none(p, "state")
    create = val_or_none(p, "create")


    ## Check input
    if not name and item == "list":
        module.fail_json(msg="Section couldn't be a list")

    ## Get key and value - I need to make decisions
    key, skey = get_uci_key(module, package, section, type, index, name)
    if key:
        val = uci_get(module, bin_path, key)
    else:
        val = None

    if not val:
        sval = uci_get(module, bin_path, skey)

    ## Handle deletes
    if state == "absent":
        if not key:
        ## User manipulates with section only
            if sval:
                uci_delete(module, bin_path, item, skey)
            else:
                module.exit_json(changed=False)
        else:
            ## User manipulates with key
            if is_set(item, val, value):
                uci_delete(module, bin_path, item, key, value)
            else:
                module.exit_json(changed=False)

    ## Handle create or update requests
    if not key:
        ## User manipulates with section only
        if not sval:
            ## ... and section doesn't exists
            if create:
                if not type:
                    module.fail_json(msg="Is necessary to create section but type wasn't specified")
                uci_set(module, bin_path, item, skey, type)
            else:
                module.fail_json(msg="Section doesn't exist.")
        else:
            ## Section exists
            module.exit_json(changed=False)
    else:
        ## User manipulates with key
        if val:
            ## Some value under key is available
            if is_set(item, val, value):
                module.exit_json(changed=False)
            else:
                uci_set(module, bin_path, item, key, value)

        elif not val and sval and create:
            ## Option doesn't exists but is possible to create it
            uci_set(module, bin_path, item, key, value)

        elif not val and sval and not create:
            module.fail_json(msg="Key doesn't exist.")

        elif not val and not sval and create:
            ## Option doesn't exists because section doesn't exists and is possible to create it
            if not type:
                module.fail_json(msg="Is necessary to create section but type wasn't specified")
            uci_set(module, bin_path, item, skey, type, noreturn=True)
            uci_set(module, bin_path, item, key, value)

        elif not val and not sval and not create:
            module.fail_json(msg="Section doesn't exist.")

        else:
            module.fail_json(msg="There is some bug in logic. Please report it.")


# import module snippets
from ansible.module_utils.basic import *

main()
