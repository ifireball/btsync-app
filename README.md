btsync-app
==========

A Linux portable [AppImage][1] builder for [BitTorrent Sync][2]

The build AppImage will include the GUI created for the 
[Debian BitTorrent Sync Package][3].

[1]: https://github.com/probonopd/appimagekit
[2]: http://www.getsync.com
[3]: https://github.com/tuxpoldo/btsync-deb

## Runtime Requirements

Ideally the AppImage created by this script would require nothing but a minimal
desktop user space on top of a Linux kernel. But for now, in order to keep the
image size down, I chose not to bundle the following components, which I assume
are available on most Linux desktops:

- Python 2
- PyGTK

## Compatibility

The AppImage is (hopefully) built in such a way that would enable it to run on
many Linux distributions. That being said, it had only been tested on Fedora 20
so far.

## Bundled Stuff

Apart from the main components mentioned above, the following libraries are also
bundled as part of the generated AppImage. There is no need to install them on
the build system as the sources are downloaded and build by the build process.

- [libqrencde](http://fukuchi.org/works/qrencode/)
- [qrencode Python library](https://pypi.python.org/pypi/qrencode)

## Build Requirements

The script in this repo is a build system. It requires the following components
to work:

- [Paver](https://pythonhosted.org/Paver/) - Available on RPM-based
  distributions as 'python-paver'
- A working internet connection - To enable the script to download additional
  stuff it needs 

