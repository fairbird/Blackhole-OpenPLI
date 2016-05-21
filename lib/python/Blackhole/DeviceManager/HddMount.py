from . import _
from enigma import *
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.ActionMap import ActionMap
from Components.MenuList import MenuList
from Components.GUIComponent import GUIComponent
from Components.HTMLComponent import HTMLComponent
from Tools.Directories import fileExists, crawlDirectory, resolveFilename
from Tools.LoadPixmap import LoadPixmap
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Button import Button
from Components.Label import Label
from Components.Sources.List import List
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from MountPoints import MountPoints
from Disks import Disks
from ExtraMessageBox import ExtraMessageBox
import os
import sys
import re

class HddMount(Screen):
    skin = '\n\t<screen name="HddMount" position="center,center" size="560,430" title="Hard Drive Mount">\n\t\t<ePixmap pixmap="/usr/share/enigma2/skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />\n\t\t<ePixmap pixmap="/usr/share/enigma2/skin_default/buttons/green.png" position="140,0" size="140,40" alphatest="on" />\n\t\t<ePixmap pixmap="/usr/share/enigma2/skin_default/buttons/yellow.png" position="280,0" size="140,40" alphatest="on" />\n\t\t<ePixmap pixmap="/usr/share/enigma2/skin_default/buttons/blue.png" position="420,0" size="140,40" alphatest="on" />\n\t\t<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />\n\t\t<widget name="key_green" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#1f771f" transparent="1" />\n\t\t<widget name="key_yellow" position="280,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#a08500" transparent="1" />\n\t\t<widget name="key_blue" position="420,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />\n\t\t<widget name="menu" position="20,45" scrollbarMode="showOnDemand" size="520,380" transparent="1" />\n\t</screen>'

    def __init__(self, session, device, partition):
        Screen.__init__(self, session)
        self.device = device
        self.partition = partition
        self.mountpoints = MountPoints()
        self.mountpoints.read()
        self.fast = False
        self.list = []
        self.list.append(_('Mount as /universe'))
        self.list.append(_('Mount as /media/usb'))
        self.list.append(_('Mount as /media/hdd'))
        self.list.append('Mount as /media/cf')
        self.list.append('Mount as /media/mmc1')
        self.list.append('Mount on custom path')
        self['menu'] = MenuList(self.list)
        self['key_red'] = Button(_('Fixed mount'))
        self['key_green'] = Button('Fast mount')
        self['key_blue'] = Button(_('Exit'))
        self['key_yellow'] = Button('')
        self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'blue': self.quit,
         'green': self.green,
         'ok': self.ok,
         'red': self.ok,
         'cancel': self.quit}, -2)
        self.onShown.append(self.setWindowTitle)

    def setWindowTitle(self):
        self.setTitle(_('Mountpoints'))

    def ok(self):
        self.fast = False
        selected = self['menu'].getSelectedIndex()
        if selected == 0:
            self.setMountPoint('/universe')
        elif selected == 1:
            self.setMountPoint('/media/usb')
        elif selected == 2:
            self.setMountPoint('/media/hdd')
        elif selected == 3:
            self.setMountPoint('/media/cf')
        elif selected == 4:
            self.setMountPoint('/media/mmc1')
        elif selected == 5:
            self.session.openWithCallback(self.customPath, VirtualKeyBoard, title=_('Insert mount point:'), text='/media/custom')

    def green(self):
        self.fast = True
        selected = self['menu'].getSelectedIndex()
        if selected == 0:
            self.setMountPoint('/universe')
        elif selected == 1:
            self.setMountPoint('/media/usb')
        elif selected == 2:
            self.setMountPoint('/media/hdd')
        elif selected == 3:
            self.setMountPoint('/media/cf')
        elif selected == 4:
            self.setMountPoint('/media/mmc1')
        elif selected == 5:
            self.session.openWithCallback(self.customPath, VirtualKeyBoard, title=_('Insert mount point:'), text='/media/custom')

    def customPath(self, result):
        if result and len(result) > 0:
            result = result.rstrip('/')
            os.system('mkdir -p %s' % result)
            self.setMountPoint(result)

    def setMountPoint(self, path):
        self.cpath = path
        if self.mountpoints.exist(path):
            self.session.openWithCallback(self.setMountPointCb, ExtraMessageBox, 'Selected mount point is already used by another drive.', 'Mount point exist!', [['Change old drive with this new drive', 'ok.png'], ['Mantain old drive', 'cancel.png']])
        else:
            self.setMountPointCb(0)

    def setMountPointCb(self, result):
        if result == 0:
            if not self.mountpoints.isMounted(self.cpath) and self.mountpoints.umount(self.cpath):
                self.session.open(MessageBox, _('Cannot umount current drive.\nA record in progress, timeshit or some external tools (like samba and nfsd) may cause this problem.\nPlease stop this actions/applications and try again'), MessageBox.TYPE_ERROR)
                self.close()
                return None
            self.mountpoints.delete(self.cpath)
            if not self.fast:
                self.mountpoints.add(self.device, self.partition, self.cpath)
            self.mountpoints.write()
            if not self.mountpoints.mount(self.device, self.partition, self.cpath):
                self.session.open(MessageBox, _('Cannot mount new drive.\nPlease check filesystem or format it and try again'), MessageBox.TYPE_ERROR)
            elif self.cpath == '/media/hdd':
                os.system('/bin/mkdir /hdd/movie')
                os.system('/bin/mkdir /hdd/music')
                os.system('/bin/mkdir /hdd/picture')
            self.close()

    def restartBox(self, answer):
        if answer is True:
            self.session.open(TryQuitMainloop, 2)
        else:
            self.close()

    def quit(self):
        self.close()


def MountEntry(description, details):
    picture = LoadPixmap('/usr/lib/enigma2/python/Blackhole/DeviceManager/icons/diskusb.png')
    return (picture, description, details)


class HddFastRemove(Screen):
    skin = '\n\t<screen name="HddFastRemove" position="center,center" size="560,430" title="Hard Drive Fast Umount">\n\t\t<ePixmap pixmap="/usr/share/enigma2/skin_default/buttons/red.png" position="0,0" size="140,40" alphatest="on" />\n\t\t<ePixmap pixmap="/usr/share/enigma2/skin_default/buttons/blue.png" position="140,0" size="140,40" alphatest="on" />\n\t\t<widget name="key_red" position="0,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />\n\t\t<widget name="key_blue" position="140,0" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#18188b" transparent="1" />\n\t\t<widget source="menu" render="Listbox" position="10,55" size="520,380" scrollbarMode="showOnDemand">\n\t\t\t<convert type="TemplatedMultiContent">\n\t\t\t\t{"template": [\n\t\t\t\t\tMultiContentEntryPixmapAlphaTest(pos = (5, 0), size = (48, 48), png = 0),\n\t\t\t\t\tMultiContentEntryText(pos = (65, 3), size = (190, 38), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 1),\n\t\t\t\t\tMultiContentEntryText(pos = (165, 27), size = (290, 38), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_TOP, text = 2),\n\t\t\t\t\t],\n\t\t\t\t\t"fonts": [gFont("Regular", 22), gFont("Regular", 18)],\n\t\t\t\t\t"itemHeight": 50\n\t\t\t\t}\n\t\t\t</convert>\n\t\t</widget>\n\t</screen>'

    def __init__(self, session):
        if disk[2] == True:
            diskname = disk[3]
            for partition in disk[5]:
                mp = ''
                rmp = ''
                try:
                    mp = self.mountpoints.get(partition[0][:3], int(partition[0][3:]))
                    rmp = self.mountpoints.getRealMount(partition[0][:3], int(partition[0][3:]))
                except Exception:
                    e = None

                if len(mp) > 0:
                    self.disks.append(MountEntry(disk[3], 'P.%s (Fixed: %s)' % (partition[0][3:], mp)))
                    self.mounts.append(mp)
                    continue
                if len(rmp) > 0:
                    self.disks.append(MountEntry(disk[3], 'P.%s (Fast: %s)' % (partition[0][3:], rmp)))
                    self.mounts.append(rmp)
                    continue
                else:
                    continue

            self.onShown.append(self.setWindowTitle)
            self['menu'] = List(self.disks)
            self['key_red'] = Button(_('Umount'))
            self['key_blue'] = Button(_('Exit'))
            self['actions'] = ActionMap(['OkCancelActions', 'ColorActions'], {'blue': self.quit,
             'red': self.red,
             'cancel': self.quit}, -2)
            return
        else:
            return

    def setWindowTitle(self):
        self.setTitle(_('Fast Mounted Remove'))

    def red(self):
        if len(self.mounts) > 0:
            self.sindex = self['menu'].getIndex()
            self.mountpoints.umount(self.mounts[self.sindex])
            self.session.open(MessageBox, _('Media unmounted'), MessageBox.TYPE_INFO)
            self.close()

    def quit(self):
        self.close()
