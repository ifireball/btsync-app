#!/usr/bin/env python
# pavement.py - Paver file fore building BtSync AppImage
#
from paver.easy import path, task, needs, sh, pushd

BUILD_DIR=path('build')
WORK_DIR=BUILD_DIR / 'tmp'
TARGET_DIR=BUILD_DIR / 'AppDir'

BTSYNC_VERSION='1.4.103'
BTSYNC_PLATFORM='x64'
BTSYNC_FILE_PATTERN='btsync_%(p)s-%(v)s.tar.gz'
BTSYNC_FILE=BTSYNC_FILE_PATTERN % { 'v': BTSYNC_VERSION, 'p': BTSYNC_PLATFORM }
BTSYNC_URL_PATTERN='http://syncapp.bittorrent.com/%(v)s/%(f)s'
BTSYNC_URL=BTSYNC_URL_PATTERN % { 'v': BTSYNC_VERSION, 'p': BTSYNC_PLATFORM, 
        'f': BTSYNC_FILE }


@task
def mk_build_dir():
    """Create directories to build the appdir in"""
    for dir in (BUILD_DIR, WORK_DIR, TARGET_DIR):
        path.mkdir(dir, 0o755)

@task
@needs('mk_build_dir')
def get_btsync_bin():
    """Download the BtSync binary"""
    with pushd(WORK_DIR):
        sh('curl -f %(u)s -o %(f)s' % {'u':BTSYNC_URL, 'f':BTSYNC_FILE})

