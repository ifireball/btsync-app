#!/usr/bin/env python
#
import sys
from os.path import dirname

def import_gi():
    old_path = list(sys.path)
    sys.path.remove(dirname(__file__))
    thismod = sys.modules.pop('gi')
    try:
        gi = __import__('gi', globals(), locals())
        thismod.sys.modules['gi'] = gi
        return True
    except ImportError:
        thismod.sys.modules['gi'] = thismod
        return False
    finally:
        thismod.sys.path = old_path

if not import_gi():
    sys.stderr.write("Gtk3 not found, falling back to Gtk2")

    import gtk as _gtk
    import gobject as _gobject
    import pango as _pango

    from types import ModuleType

    repository = ModuleType('repository')
    sys.modules['gi.repository'] = repository

    repository.Gtk = _gtk
    repository.GObject = _gobject
    repository.Gdk = _gtk.gdk
    repository.Pango = _pango
    repository.GdkPixbuf = _gtk.gdk.Pixbuf

    repository.Gtk.MessageType.INFO     = _gtk.MESSAGE_INFO
    repository.Gtk.MessageType.ERROR    = _gtk.MESSAGE_ERROR
    repository.Gtk.MessageType.WARNING  = _gtk.MESSAGE_WARNING
    repository.Gtk.MessageType.QUESTION = _gtk.MESSAGE_QUESTION
    repository.Gtk.MessageType.OTHER    = _gtk.MESSAGE_OTHER

    repository.Gtk.ButtonsType.CANCEL    = _gtk.BUTTONS_CANCEL
    repository.Gtk.ButtonsType.CLOSE     = _gtk.BUTTONS_CLOSE
    repository.Gtk.ButtonsType.NONE      = _gtk.BUTTONS_NONE
    repository.Gtk.ButtonsType.OK        = _gtk.BUTTONS_OK
    repository.Gtk.ButtonsType.OK_CANCEL = _gtk.BUTTONS_OK_CANCEL
    repository.Gtk.ButtonsType.YES_NO    = _gtk.BUTTONS_YES_NO

    class _StatusIcon(_gtk.StatusIcon):
        def set_name(self, name):
            pass

    class _MenuItem(_gtk.MenuItem):
        def set_visible(self, v):
            pass

    class _Builder(_gtk.Builder):
        _overrides = {
            _gtk.StatusIcon: _StatusIcon,
            _gtk.MenuItem: _MenuItem,
        }
        def get_object(self, name):
            o = super(self.__class__, self).get_object(name)
            o.__class__ = self._overrides.get(type(o), type(o))
            return o

    _gtk.StatusIcon = _StatusIcon
    _gtk.MenuItem = _MenuItem
    _gtk.Builder = _Builder
