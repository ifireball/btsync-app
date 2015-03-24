#!/usr/bin/env python
# ldd.py - Python wrapper around ldd
#
import subprocess 
import re
import sys

if hasattr(subprocess, 'check_output'):
    check_output = subprocess.check_output
else:
    def check_output(args):
        p = subprocess.Popen(args, close_fds = True, stdout = subprocess.PIPE)
        output, unused_err = p.communicate()
        retcode = p.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, args, output=output)
        return output

def ldd(binary):
    """Run the ldd program on the given binary file returning output as a
    dictionary
    """
    r = re.compile('^\s*(.+)\s+=>\s+(.*)\s+\(0x[0-9a-zA-Z]+\)$')
    out = {}
    for line in check_output(('ldd', str(binary))).splitlines():
        m = r.match(line) 
        if not m:
            continue
        lib, path = m.groups()
        out[lib] = path
    return out

def findlib(library, binary):
    """Find the path to the given library that is in use by the given executable
    binary. Library names can be approximated and not include version or file
    extensions"""
    lls = ldd(binary)
    if library in lls:
        return lls[library]
    else:
        m = (library.endswith('.') and library or library + '.')
        for l, p in lls.iteritems():
            if l.startswith(m):
                return p
            
def findlibc(binary = sys.executable):
    """Find the path to the libc library used by the given executable"""
    return findlib('libc', binary)

