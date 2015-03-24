#!/usr/bin/env python
# pavement.py - Paver file fore building BtSync AppImage
#
import sys
if not '' in sys.path:
    sys.path.insert(0, '')

import re
from os import environ
from paver.easy import path, task, needs, sh, pushd
from version import get_git_version
from ldd import findlibc

BUILD_DIR=path('build')
WORK_DIR=BUILD_DIR / 'tmp'
TARGET_DIR=BUILD_DIR / 'AppDir'
BUILD_PREFIX='/_nowhere_'
TARGET_PREFIX=TARGET_DIR / 'usr'
DIR_MODE=0755
EXE_MODE=0755
PLATFORM='x86_64'
VERSION=get_git_version()

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
    def __init__(self, version='1.4.103', platform=PLATFORM, workdir=WORK_DIR,
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
        self.patch = path('btsync_deb_appindicator_path.patch')

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

class PythonQREncode(Package):
    def __init__(self, version='1.01', workdir=WORK_DIR, tagretdir=TARGET_DIR):
        super(PythonQREncode, self).__init__(version=version,
                remote_name='qrencode',
                urlbase='https://pypi.python.org/packages/source/q/qrencode',
                workdir=workdir)
        self.patch = path('python_qrencode_fix_pillow_import.patch')

class Urllib3(Package):
    def __init__(self, version='1.8.2', workdir=WORK_DIR, tagretdir=TARGET_DIR):
        super(Urllib3, self).__init__(version=version,
                urlbase='https://pypi.python.org/packages/source/u/urllib3',
                workdir=workdir)

class Requests(Package):
    def __init__(self, version='1.2.3', workdir=WORK_DIR, tagretdir=TARGET_DIR):
        super(Requests, self).__init__(version=version,
                urlbase='https://pypi.python.org/packages/source/r/requests',
                workdir=workdir)

class AppImageKit(Package):
    def __init__(self, tag='1', workdir=WORK_DIR):
        super(AppImageKit, self).__init__(version=tag, 
                url='https://codeload.github.com/probonopd/AppImageKit/tar.gz/' +
                tag, workdir=workdir)
        self.patch = path('appimagekit_fix_icontheme.patch')
        self.package_tool = self.extract_path / 'AppImageAssistant.AppDir' /\
                'package'
        self.libc_wrap_gen_path = self.extract_path / 'LibcWrapGenerator'
        self.libc_wrap_gen_src = self.libc_wrap_gen_path /\
                'LibcWrapGenerator.vala'
        self.libc_wrap_gen = self.libc_wrap_gen_path / 'LibcWrapGenerator'
        self.libc_wrap_h = self.libc_wrap_gen_path / 'libcwrap.h'

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
@needs('mk_build_dir')
def get_python_urllib3_src():
    """Download and extract python-urllib3 sources"""
    Urllib3().download_and_extract()

@task
@needs('mk_build_dir')
def get_python_requests_src():
    """Download and extract python-requests sources"""
    Requests().download_and_extract()

@task
@needs('mk_build_dir')
def get_appimagekit_src():
    """Checkout AppImageKit source from Github"""
    AppImageKit().download_and_extract()

@task
@needs('get_btsync_deb_src')
def build_btsync_gui():
    """Build the BySync GUI"""
    btsd=BTSyncDeb()
    locdir = btsd.gui_path / 'locale'
    locdir.mkdir(DIR_MODE)
    for pofile in (btsd.gui_path / 'po').glob('*.po'):
        dstdir = locdir
        for sd in (pofile.namebase, 'LC_MESSAGES'):
            dstdir = dstdir / sd
            dstdir.mkdir(DIR_MODE)
        sh("msgfmt -c '%s' -o '%s'" % (pofile, dstdir / 'btsync-gu.mo'))
    patchabs = btsd.patch.abspath()
    with pushd(btsd.extract_path):
        sh("patch -p1 < '%s'" % (patchabs))

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
@needs('get_python_urllib3_src')
def build_python_urllib3():
    """Build the python-urllib3 library"""
    pl = Urllib3()
    with pushd(pl.extract_path):
        sh("python setup.py build")

@task
@needs('get_python_requests_src')
def build_python_requests():
    """Build the python-requests library"""
    pl = Requests()
    with pushd(pl.extract_path):
        sh("python setup.py build")

@task
@needs('get_appimagekit_src')
def build_appimagekit():
    """Build the AppImahgeKit"""
    aik = AppImageKit()
    lcwgsabs = aik.libc_wrap_gen_src.abspath()
    with pushd(aik.libc_wrap_gen_path):
        sh("valac --pkg gee-0.8 --pkg posix --pkg glib-2.0 --pkg gio-2.0 '%s'" %
                (lcwgsabs,))
    libdir = path(findlibc(aik.libc_wrap_gen)).dirname()
    sh("%s --target 2.7 --libdir '%s' --output '%s'" % \
            (aik.libc_wrap_gen, libdir, aik.libc_wrap_h))
    environ['CC'] = "gcc -U_FORTIFY_SOURCE -include '%s'" % \
            (aik.libc_wrap_h.abspath(),)
    patchabs = aik.patch.abspath()
    with pushd(aik.extract_path):
        sh("patch -p1 < '%s'" % (patchabs,))
        sh("cmake .")
        sh('rm -f AppImageAssistant')
        sh('make AppImageAssistant')


@task
@needs('build_btsync_gui')
def install_btsync_gui():
    """Install the BTSync GUI files to the AppDir"""
    btsd=BTSyncDeb()
    with open(btsd.install_file, 'r') as f:
        for l in f:
            if re.match('^\s*(#|$)', l):
                continue
            src, dst = l.split()
            src = btsd.gui_path / src
            # The *.desktop file goes to the AppDir root to AppImageKit will
            # find it
            if src.ext == '.desktop':
                dst = TARGET_DIR
            else:
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
    path('btsync-api-token.txt').copy(btsync.key_target_path)

@task
@needs('mk_build_dir')
def install_apprun():
    """Install the AppRun script in the AppDir"""
    sh("install -m %o '%s' '%s'" % (EXE_MODE, 'AppRun', TARGET_DIR / 'AppRun'))

@task
@needs('build_qrencode')
def install_qrencode():
    """Instrall the qrencode library"""
    abstgt=TARGET_PREFIX.abspath()
    with pushd(QREncode().extract_path):
        sh('make prefix=%s install' % (abstgt))
    
@task
@needs('build_python_qrencode')
def install_python_qrencode():
    """Install the qrencode Python bindings"""
    abstgt=TARGET_PREFIX.abspath()
    abslib=(TARGET_PREFIX / 'lib' / 'python').abspath()
    with pushd(PythonQREncode().extract_path):
        sh("python setup.py install --home='%s' --install-lib='%s'" % (abstgt,
            abslib))
    
@task
@needs('build_python_urllib3')
def install_python_urllib3():
    """Install the urllib3 Python library"""
    abstgt=TARGET_PREFIX.abspath()
    abslib=(TARGET_PREFIX / 'lib' / 'python').abspath()
    environ['PYTHONPATH'] = (environ.has_key('PYTHONPATH') and
            environ['PYTHONPATH'] + ':' or '') + abslib
    with pushd(Urllib3().extract_path):
        sh("python setup.py install --home='%s' --install-lib='%s'" % (abstgt,
            abslib))
    
@task
@needs('build_python_requests')
def install_python_requests():
    """Install the requests Python library"""
    abstgt=TARGET_PREFIX.abspath()
    abslib=(TARGET_PREFIX / 'lib' / 'python').abspath()
    environ['PYTHONPATH'] = (environ.has_key('PYTHONPATH') and
            environ['PYTHONPATH'] + ':' or '') + abslib
    with pushd(Requests().extract_path):
        sh("python setup.py install --home='%s' --install-lib='%s'" % (abstgt,
            abslib))
    
@task
@needs(['install_python_qrencode', 'install_python_urllib3',
    'install_python_requests', 'install_btsync_gui', 'install_btsync_bin',
    'install_api_token', 'install_apprun'])
def install():
    """Install everything to the AppDir"""
    pass

@task
@needs(['install', 'build_appimagekit'])
def mk_appimage():
    """Create an AppImage containing the app and all dependencies"""
    pt = AppImageKit().package_tool
    target = BUILD_DIR / ('btsync-app-%s-%s' % (PLATFORM, VERSION))
    sh("%s '%s' '%s'" % (pt, TARGET_DIR, target))


@task
def clean():
    """Delete all build artifacts"""
    sh("rm -rf '%s'" % (BUILD_DIR))
