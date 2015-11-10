# cinder-auto-snapshot
Python based script that creates snapshots and deletes old snapshots to perform tasks similar to a backup software.
Tested on OpenStack Kilo

Any improvements are welcome, feel free to create a pull request.

## Status
[![Build Status](https://travis-ci.org/crystone/cinder-auto-snapshot.svg?branch=master)](https://travis-ci.org/crystone/cinder-auto-snapshot)

## Requirements
See requirements.txt for pip requirements, use 'pip install -r requirements.txt' to install requirements using pip or use your package manager.

If you don't have pip, use 'easy_install pip' to install pip.

* python 2.6 or 2.7
* python-cinderclient

## Installation
* Make sure /etc/cinder and /var/log/cinder folders exists.
* Copy sample config file to /etc/cinder
* Copy the cinder-auto-snapshot.py file to where you wanna have it, we recommend something like /usr/local/sbin.

You can now run the script manually or add a cron job to run it, check the log file for any errors.

## Example cron job
/etc/cron.d/cinder-auto-snapshot
```
# Performs cinder snapshots using cinder-auto-snapshot
0 1 * * * root if [ -x /usr/local/sbin/cinder-auto-snapshot ] ; then /usr/local/sbin/cinder-auto-snapshot >/dev/null 2>&1; fi
```

## License
cinder-auto-snapshot
Copyright (C) 2015 Crystone Sverige AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
