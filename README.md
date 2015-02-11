btsync-app [![Build Status][4]][5]
==========

A Linux portable [AppImage][1] builder for [BitTorrent Sync][2]

The built AppImage will include the GUI created for the 
[Debian BitTorrent Sync Package][3].

[1]: https://github.com/probonopd/appimagekit
[2]: http://www.getsync.com
[3]: https://github.com/tuxpoldo/btsync-deb
[4]: https://travis-ci.org/ifireball/btsync-app.svg?branch=master
[5]: https://travis-ci.org/ifireball/btsync-app

## Compatibility

The AppImage is (hopefully) built in such a way that would enable it to run on
many Linux distributions. That being said, it had only been tested on Fedora 20
so far.

Binary components included in the AppImage are currtly compatible only with
64bit intel-based processors (x86-64). Patches to add components for other
platforms are welcome.

Ideally the AppImage created by this script would require nothing but a minimal
desktop user space on top of a Linux kernel. But for now, in order to keep the
image size down, I chose not to bundle the following components, which I assume
are available on most Linux desktops:

- Python 2
- PyGTK

## Bundled Stuff

Apart from the main components mentioned above, the following libraries are also
bundled as part of the generated AppImage. There is no need to install them on
the build system as the sources are downloaded and built by the build process.

- [libqrencde](http://fukuchi.org/works/qrencode/)
- [qrencode Python library](https://pypi.python.org/pypi/qrencode)
- [urllib3 Python library](https://pypi.python.org/pypi/urllib3)
- [requests Python library](http://docs.python-requests.org/en/latest/)

## Build Requirements

The script in this repo is a build system. It requires the following components
to work:

- [Paver](https://pythonhosted.org/Paver/) - Available on RPM-based
  distributions as 'python-paver'
- C compilation toolchain - For building Python extention libraries
- [cmake](http://www.cmake.org/) - For building AppImageKit
- [fuse](http://fuse.sourceforge.net/) development libraries - Also for
  AppImageKit. It avalable as the 'fuse-devel' PRM package
- A working internet connection - To enable the script to download additional
  stuff it needs 

## Building and running

To build the AppImage, run the following command:

    paver mk_appimage

Once the build process in done, the AppImage would be in the following path:

    build/btsync-app-x86_64-0.1.0

The AppImage is a binary executable file, it can be copied and run anywhere.
