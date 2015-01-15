#!/usr/bin/env python
# pavement.py - Paver file fore building BtSync AppImage
#
from paver.easy import path, task, needs, sh, pushd
import re

BUILD_DIR=path('build')
WORK_DIR=BUILD_DIR / 'tmp'
TARGET_DIR=BUILD_DIR / 'AppDir'
DIR_MODE=0755
EXE_MODE=0755

class Package:
    """Class for handling software packages"""

    def __init__(self, version, name=None, 
            remote_name=None, remote_prefix=None, 
            local_name=None, local_prefix=None, 
            url=None, urlbase=None,
            workdir=WORK_DIR, dir_in_archive=True, dirmode=DIR_MODE):
        assert url or urlbase
        self.remote_name = (remote_prefix and remote_prefix + '-' or '') + \
                (remote_name or name or self.name_from_class()) + '-' + version
        self.local_name = (local_prefix and local_prefix + '-' or '') + \
                (local_name or name or self.name_from_class()) + '-' + version
        self.remote_archive_name = self.remote_name + '.tar.gz'
        self.local_archive_name = self.local_name + '.tar.gz'
        self.url = url or (urlbase + '/' + self.remote_archive_name)
        self.local_archive_path = wordir / self.local_archive_name
        self.extract_path = workdir / self.local_name
        self._dirmode = dirmode
        self._dir_in_archive = dir_in_archive

    def download_and_extract(self):
        """Download and extract the package"""
        sh("curl -f '%s' -o '%s'" % (self.url, self.local_archive_path))
        if self._dir_in_archive:
            btsync.extract_path.mkdir(self._dirmode)
        sh("tar -xvzf '%s' -C '%s'" % (btsync.local_archive_path, btsync.extract_path))


class BtSync:
    def __init__(self, version='1.4.103', platform='x86_64', workdir=WORK_DIR,
            targetdir=TARGET_DIR):
        self.platform = platform
        self.platform_nic = { 'x86_64': 'x64' }.get(self.platform, self.platform)
        self.file_base_name = 'btsync_%s-%s' % (self.platform_nic, version)
        self.archive_name = self.file_base_name + '.tar.gz'
        self.archive_path = workdir / self.archive_name
        self.url ='http://syncapp.bittorrent.com/%s/%s' % (version,
                self.archive_name)
        self.extract_path = workdir / self.file_base_name
        self.binary_src_path = self.extract_path / 'btsync'
        self.binary_target_dir = targetdir / 'usr' / 'lib' / 'btsync-common'
        self.binary_target_path = self.binary_target_dir / 'btsync-core'
        self.key_target_dir = targetdir / 'usr' / 'lib' / 'btsync-gui'
        self.key_target_path = self.key_target_dir / 'btsync-gui.key'

class BtSyncDeb:
    def __init__(self, tag='btsync-1.4.1-1', workdir=WORK_DIR):
        self.file_base_name = 'btsync-deb-' + tag
        self.archive_name = self.file_base_name + '.zip'
        self.archive_path = workdir / self.archive_name
        self.url = \
            'https://codeload.github.com/tuxpoldo/btsync-deb/tar.gz/' + tag
        self.extract_path = workdir / self.file_base_name
        self.gui_path = self.extract_path / 'btsync-gui'
        self.install_file = self.gui_path / 'debian' / 'btsync-gui-gtk.install'

class python_qrencode:
    def __init__(self, version='1.01', workdir=WORK_DIR, tagretdir=TARGET_DIR):
        self.file_base_name = 'qrencode-' + version
        self.archive_name = self.file_base_name + '.tar.gz'
        self.archive_path = workdir / self.archive_name
        self.url = 'https://pypi.python.org/packages/source/q/qrencode' + \
                self.archive_name
        self.extract_path = workdir / self.file_base_name

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
    sh("curl -f '%s' -o '%s'" % (btsync.url, btsync.archive_path))
    btsync.extract_path.mkdir(DIR_MODE)
    sh("tar -xvzf '%s' -C '%s'" % (btsync.archive_path, btsync.extract_path))

@task
@needs('mk_build_dir')
def get_btsync_deb_src():
    """Checkout btsync-deb source from Github"""
    btsd=BtSyncDeb()
    sh("curl -f '%s' -o '%s'" % (btsd.url, btsd.archive_path))
    sh("tar -xvzf '%s' -C '%s'" % (btsd.archive_path, WORK_DIR))

@task
@needs('get_btsync_deb_src')
def build_btsync_gui_locales():
    """Build the BySync GUI locale files"""
    btsd=BtSyncDeb()
    locdir = btsd.gui_path / 'locale'
    locdir.mkdir(DIR_MODE)
    for pofile in (btsd.gui_path / 'po').glob('*.po'):
        dstdir = locdir
        for sd in (pofile.namebase, 'LC_MESSAGES'):
            dstdir = dstdir / sd
            dstdir.mkdir(DIR_MODE)
        sh("msgfmt -c '%s' -o '%s'" % (pofile, dstdir / 'btsync-gu.mo'))

@task
@needs('build_btsync_gui_locales')
def install_btsync_gui():
    """Install the BtSync GUI files to the AppDir"""
    btsd=BtSyncDeb()
    with open(btsd.install_file, 'r') as f:
        for l in f:
            if re.match('^\s*(#|$)', l):
                continue
            src, dst = l.split()
            src = btsd.gui_path / src
            dst = TARGET_DIR / dst
            dst.makedirs(DIR_MODE)
            sh("cp --preserve=mode -frt '%s' '%s'" % (dst, src))

@task
@needs('get_btsync_bin')
def install_btsync_bin():
    """Install the BtSync binary to the AppDir"""
    btsync = BtSync()
    btsync.binary_target_dir.makedirs(DIR_MODE)
    sh("install -m %o '%s' '%s'" % (EXE_MODE, btsync.binary_src_path,
        btsync.binary_target_path))

@task
@needs('mk_build_dir')
def install_api_token():
    """Install the API token to the AppDir"""
    btsync = BtSync()
    btsync.key_target_dir.makedirs(DIR_MODE)
    path('btsync-api-token.txt').copyfile(btsync.key_target_path)

@task
@needs('mk_build_dir')
def install_apprun():
    """Install the AppRun script in the AppDir"""
    sh("install -m %o '%s' '%s'" % (EXE_MODE, 'AppRun', TARGET_DIR / 'AppRun'))
    
@task
@needs(['install_btsync_gui', 'install_btsync_bin', 'install_api_token',
    'install_apprun'])
def install():
    """Install everything to the AppDir"""
    pass
