#!/usr/bin/env python
# pavement.py - Paver file fore building BtSync AppImage
#
import re
from os import environ
from paver.easy import path, task, needs, sh, pushd

BUILD_DIR=path('build')
WORK_DIR=BUILD_DIR / 'tmp'
TARGET_DIR=BUILD_DIR / 'AppDir'
BUILD_PREFIX='/_nowhere_'
TARGET_PREFIX=TARGET_DIR / 'usr'
DIR_MODE=0755
EXE_MODE=0755

class Package(object):
    """Class for handling software packages"""

    def __init__(self, version, workdir, name=None, 
            remote_name=None, remote_prefix=None, 
            local_name=None, local_prefix=None, 
            url=None, urlbase=None,
            dir_in_archive=True, dirmode=DIR_MODE):
        assert url or urlbase
        self.remote_name = (remote_prefix and remote_prefix + '-' or '') + \
                (remote_name or name or self.name_from_class()) + '-' + version
        self.local_name = (local_prefix and local_prefix + '-' or '') + \
                (local_name or name or self.name_from_class()) + '-' + version
        self.remote_archive_name = self.remote_name + '.tar.gz'
        self.local_archive_name = self.local_name + '.tar.gz'
        self.url = url or (urlbase + '/' + self.remote_archive_name)
        self.local_archive_path = workdir / self.local_archive_name
        self.extract_path = workdir / self.local_name
        self._strip_components = dir_in_archive and 1 or 0
        self._dirmode = dirmode

    def download(self):
        """Download the package"""
        sh("curl -f '%s' -o '%s'" % (self.url, self.local_archive_path))

    def extract(self):
        """Extract the packge"""
        self.extract_path.mkdir(self._dirmode)
        sh("tar -xvzf '%s' -C '%s' --strip-components=%d" % (\
                self.local_archive_path, self.extract_path,
                self._strip_components))

    def download_and_extract(self):
        """Download and extract the package"""
        self.download()
        self.extract()

    def name_from_class(self):
        """Convert class name into a package name.
        Conversion is done by lowercasing all caps and adding dashes in front
        of them when they follow lowercase letters.
        For example:

        BTSyncDeb => btsync-deb
        """
        return re.sub('([a-z]?)([A-Z])',
                lambda m: (m.group(1) and m.group(1) + '-') + \
                        m.group(2).lower(), 
                self.__class__.__name__)

class BTSync(Package):
    def __init__(self, version='1.4.103', platform='x86_64', workdir=WORK_DIR,
            targetdir=TARGET_DIR, dirmode=DIR_MODE):
        self.platform = platform
        self.platform_nic = { 'x86_64': 'x64' }.get(self.platform, self.platform)
        super(BTSync, self).__init__(version=version,
                name='btsync_' + self.platform_nic,
                urlbase='http://syncapp.bittorrent.com/' + version,
                dir_in_archive=False, workdir=workdir, dirmode=dirmode)
        self.binary_src_path = self.extract_path / 'btsync'
        self.binary_target_dir = targetdir / 'usr' / 'lib' / 'btsync-common'
        self.binary_target_path = self.binary_target_dir / 'btsync-core'
        self.key_target_dir = targetdir / 'usr' / 'lib' / 'btsync-gui'
        self.key_target_path = self.key_target_dir / 'btsync-gui.key'

class BTSyncDeb(Package):
    def __init__(self, tag='btsync-1.4.1-1', workdir=WORK_DIR):
        super(BTSyncDeb, self).__init__(version=tag, 
                url='https://codeload.github.com/tuxpoldo/btsync-deb/tar.gz/' +
                tag, workdir=workdir)
        self.gui_path = self.extract_path / 'btsync-gui'
        self.install_file = self.gui_path / 'debian' / 'btsync-gui-gtk.install'

class QREncode(Package):
    def __init__(self, version='3.4.4', workdir=WORK_DIR):
        super(QREncode, self).__init__(version=version,
                urlbase='http://fukuchi.org/works/qrencode',
                workdir=workdir)

class PythonQREncode(Package):
    def __init__(self, version='1.01', workdir=WORK_DIR, tagretdir=TARGET_DIR):
        super(PythonQREncode, self).__init__(version=version,
                remote_name='qrencode',
                urlbase='https://pypi.python.org/packages/source/q/qrencode',
                workdir=workdir)
        self.patch = path('python_qrencode_fix_pillow_import.patch')

@task
def mk_build_dir():
    """Create directories to build the appdir in"""
    for d in (BUILD_DIR, WORK_DIR, TARGET_DIR):
        d.mkdir(DIR_MODE)

@task
@needs('mk_build_dir')
def get_btsync_bin():
    """Download the BtSync binary"""
    BTSync().download_and_extract()

@task
@needs('mk_build_dir')
def get_btsync_deb_src():
    """Checkout btsync-deb source from Github"""
    BTSyncDeb().download_and_extract()

@task
@needs('mk_build_dir')
def get_qrencode_src():
    """Download and extract qrencode sources"""
    QREncode().download_and_extract()

@task
@needs('mk_build_dir')
def get_python_qrencode_src():
    """Download and extract python-qrencode sources"""
    PythonQREncode().download_and_extract()

@task
@needs('get_btsync_deb_src')
def build_btsync_gui_locales():
    """Build the BySync GUI locale files"""
    btsd=BTSyncDeb()
    locdir = btsd.gui_path / 'locale'
    locdir.mkdir(DIR_MODE)
    for pofile in (btsd.gui_path / 'po').glob('*.po'):
        dstdir = locdir
        for sd in (pofile.namebase, 'LC_MESSAGES'):
            dstdir = dstdir / sd
            dstdir.mkdir(DIR_MODE)
        sh("msgfmt -c '%s' -o '%s'" % (pofile, dstdir / 'btsync-gu.mo'))

@task
@needs('get_qrencode_src')
def build_qrencode():
    """Build the qrencode library"""
    with pushd(QREncode().extract_path):
        sh("./configure --without-tools --without-tests --prefix='%s'" % \
                (BUILD_PREFIX))
        sh('make')

@task
@needs('get_python_qrencode_src', 'install_qrencode')
def build_python_qrencode():
    """Build the python-qrencode library"""
    pqre = PythonQREncode()
    include_dir = (TARGET_PREFIX / 'include').abspath()
    lib_dir = (TARGET_PREFIX / 'lib').abspath()
    environ['CFLAGS'] = '-I' + include_dir
    environ['LDFLAGS'] = '-L' + lib_dir
    patchabs = pqre.patch.abspath()
    with pushd(pqre.extract_path):
        sh("patch -p1 < '%s'" % (patchabs))
        sh("python setup.py build")

@task
@needs('build_btsync_gui_locales')
def install_btsync_gui():
    """Install the BTSync GUI files to the AppDir"""
    btsd=BTSyncDeb()
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
    """Install the BTSync binary to the AppDir"""
    btsync = BTSync()
    btsync.binary_target_dir.makedirs(DIR_MODE)
    sh("install -m %o '%s' '%s'" % (EXE_MODE, btsync.binary_src_path,
        btsync.binary_target_path))

@task
@needs('mk_build_dir')
def install_api_token():
    """Install the API token to the AppDir"""
    btsync = BTSync()
    btsync.key_target_dir.makedirs(DIR_MODE)
    path('btsync-api-token.txt').copyfile(btsync.key_target_path)

@task
@needs('mk_build_dir')
def install_apprun():
    """Install the AppRun script in the AppDir"""
    sh("install -m %o '%s' '%s'" % (EXE_MODE, 'AppRun', TARGET_DIR / 'AppRun'))

@task
@needs('build_qrencode')
def install_qrencode():
    abstgt=TARGET_PREFIX.abspath()
    with pushd(QREncode().extract_path):
        sh('make prefix=%s install' % (abstgt))
    
@task
@needs('build_python_qrencode')
def install_python_qrencode():
    abstgt=TARGET_PREFIX.abspath()
    abslib=(TARGET_PREFIX / 'lib' / 'python').abspath()
    with pushd(PythonQREncode().extract_path):
        sh("python setup.py install --home='%s' --install-lib='%s'" % (abstgt,
            abslib))
    
@task
@needs(['install_python_qrencode', 'install_btsync_gui', 'install_btsync_bin',
    'install_api_token', 'install_apprun'])
def install():
    """Install everything to the AppDir"""
    pass
