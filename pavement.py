#!/usr/bin/env python
# pavement.py - Paver file fore building BtSync AppImage
#
from paver.easy import path, task, needs, sh, pushd

BUILD_DIR=path('build')
WORK_DIR=BUILD_DIR / 'tmp'
TARGET_DIR=BUILD_DIR / 'AppDir'
DIR_MODE=0755

class BtSync:
    def __init__(self, version='1.4.103', platform='x86_64', workdir=WORK_DIR):
        self.version = version
        self.platform = platform
        self.platform_nic = { 'x86_64': 'x64' }.get(self.platform, self.platform)
        self.file_base_name = 'btsync_%s-%s' % (self.platform_nic, self.version)
        self.archive_name = self.file_base_name + '.tar.gz'
        self.archive_path = workdir / self.archive_name
        self.url ='http://syncapp.bittorrent.com/%s/%s' % (self.version,
                self.archive_name)
        self.extract_path = workdir / self.file_base_name

class BtSyncDeb:
    def __init__(self, tag='btsync-1.4.1-1', workdir=WORK_DIR):
        self.tag = tag
        self.file_base_name = 'btsync-deb-' + self.tag
        self.archive_name = self.file_base_name + '.zip'
        self.archive_path = workdir / self.archive_name
        self.url = 'https://codeload.github.com/tuxpoldo/btsync-deb/tar.gz/%s' % (
                self.tag)
        self.extract_path = workdir / self.file_base_name
        self.gui_path = self.extract_path / 'btsync-gui'

@task
def mk_build_dir():
    """Create directories to build the appdir in"""
    for d in (BUILD_DIR, WORK_DIR, TARGET_DIR):
        d.mkdir(DIR_MODE)

@task
@needs('mk_build_dir')
def get_btsync_bin():
    """Download the BtSync binary"""
    btsync = BtSync()
    sh('curl -f %s -o %s' % (btsync.url, btsync.archive_path))
    btsync.extract_path.mkdir(DIR_MODE)
    sh('tar -xvzf %s -C %s' % (btsync.archive_path, btsync.extract_path))

@task
@needs('mk_build_dir')
def get_btsync_deb_src():
    """Checkout btsync-deb source from Github"""
    btsd=BtSyncDeb()
    sh('curl -f %s -o %s' % (btsd.url, btsd.archive_path))
    sh('tar -xvzf %s -C %s' % (btsd.archive_path, WORK_DIR))

@task
@needs('get_btsync_deb_src')
def build_btsync_gui_locales():
    """Build the BySyunc GUI locale files"""
    btsd=BtSyncDeb()
    locdir = btsd.gui_path / 'locale'
    locdir.mkdir(DIR_MODE)
    for pofile in (btsd.gui_path / 'po').glob('*.po'):
        dstdir = locdir
        for sd in (pofile.namebase, 'LC_MESSAGES'):
            dstdir = dstdir / sd
            dstdir.mkdir(DIR_MODE)
        sh('msgfmt -c %s -o %s' % (pofile, dstdir / 'btsync-gu.mo'))


