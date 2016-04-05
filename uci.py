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

def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(aliases=["key"], required=True)
        )
    )


# import module snippets
from ansible.module_utils.basic import *

main()
