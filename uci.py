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


def val_or_none(params, key):
    if key not in params:
        return None

    return params[key]


def get_uci_key(package, section, type, index, name):
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


def uci_commit(module, binary, package):
    status, stdout, stderr = module.run_command("{} commit {}".format(binary, package))
    if status != 0:
        module.fail_json(msg="Commit failed with: {}".format(stderr))


def uci_delete(module, binary, key):
    status, stdout, stderr = module.run_command("{} delete {}".format(binary, key))
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


def uci_set(module, binary, key, value, noreturn=False):
    if not value:
        module.fail_json(msg="Value wasn't provided")

    status, stdout, stderr = module.run_command("{} set {}='{}'".format(binary, key, value))
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
            index = dict(required=False),
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

    ## Report unimplemented features
    if item == "list":
        module.fail_json(msg="Item of type 'list' is unimplemented for now")

    ## Get key and value - I need to make decisions
    key, skey = get_uci_key(package, section, type, index, name)
    val = uci_get(module, bin_path, key)

    ## Handle deletes
    if state == "absent":
        if not val:
            module.exit_json(changed=False)
        else:
            uci_delete(module, bin_path, key)

    ## Handle create or update requests
    if not val and not create:
        module.fail_json(msg="Key doesn't exist.")

    if not val and create:
        module.fail_json(msg="TODO: Create intermediates")

    if val and not value:
        module.fail_json(msg="Value wasn't provided")

    if val and value:
        if val == value:
            module.exit_json(changed=False)
        else:
            uci_set(module, bin_path, key, p["value"])


# import module snippets
from ansible.module_utils.basic import *

main()
