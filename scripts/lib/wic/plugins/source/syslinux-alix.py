# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
#
# Copyright (c) 2014, Intel Corporation.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# DESCRIPTION
# This implements the 'syslinux-alix' source plugin class for 'wic'.
# This plugin is a modified version of bootimg-pcbios by Tomi Zanussi.
#
# AUTHORS
# Tom Zanussi <tom.zanussi (at] linux.intel.com>
# modified by Krisztian Litkey <krisztian litkey@intel.com>
#

import logging
import os

from wic import WicError
from wic.engine import get_custom_config
from wic.pluginbase import SourcePlugin
from wic.misc import (exec_cmd, exec_native_cmd,
                      get_bitbake_var, BOOTDD_EXTRA_SPACE)

logger = logging.getLogger('wic')

class SyslinuxAlixPlugin(SourcePlugin):
    """
    Create MBR boot partition and install syslinux on it.
    """

    name = 'syslinux-alix'

    @classmethod
    def _get_bootimg_dir(cls, bootimg_dir, dirname):
        """
        Check if dirname exists in default bootimg_dir or in STAGING_DIR.
        """
        for result in (bootimg_dir, get_bitbake_var("STAGING_DATADIR")):
            if os.path.exists("%s/%s" % (result, dirname)):
                return result

        raise WicError("Couldn't find correct bootimg_dir, exiting")

    @classmethod
    def do_install_disk(cls, disk, disk_name, creator, workdir, oe_builddir,
                        bootimg_dir, kernel_dir, native_sysroot):
        """
        Called after all partitions have been prepared and assembled into a
        disk image.  In this case, we install the MBR.
        """
        bootimg_dir = cls._get_bootimg_dir(bootimg_dir, 'syslinux')
        mbrfile = "%s/syslinux/" % bootimg_dir
        if creator.ptable_format == 'msdos':
            mbrfile += "mbr.bin"
        elif creator.ptable_format == 'gpt':
            mbrfile += "gptmbr.bin"
        else:
            raise WicError("Unsupported partition table: %s" %
                           creator.ptable_format)

        if not os.path.exists(mbrfile):
            raise WicError("Couldn't find %s.  If using the -e option, do you "
                           "have the right MACHINE set in local.conf?  If not, "
                           "is the bootimg_dir path correct?" % mbrfile)

        full_path = creator._full_path(workdir, disk_name, "direct")
        logger.debug("Installing MBR on disk %s as %s with size %s bytes",
                     disk_name, full_path, disk.min_size)

        dd_cmd = "dd if=%s of=%s conv=notrunc" % (mbrfile, full_path)
        exec_cmd(dd_cmd, native_sysroot)

    @classmethod
    def _syslinux_config(cls, bootloader):
        """
        Generate syslinux configuration or take a custom one as such.
        """
        custom = None
        if bootloader.configfile:
            custom = get_custom_config(bootloader.configfile)
            if custom:
                logger.debug("Using custom configuration file %s "
                             "for syslinux.cfg", bootloader.configfile)
                return custom
            else:
                raise WicError("configfile is specified but failed to "
                               "get it from %s." % bootloader.configfile)

        # We try to comply to the stock syslinux.bbclass for the basic
        # configuration variables.
        serial = get_bitbake_var("SYSLINUX_SERIAL")
        serial_tty = get_bitbake_var("SYSLINUX_SERIAL_TTY")
        prompt = get_bitbake_var("SYSLINUX_PROMPT")
        timeout = get_bitbake_var("SYSLINUX_TIMEOUT")
        allow_options = get_bitbake_var("SYSLINUX_ALLOWOPTIONS")
        initrd = ("initrd=/initrd" if get_bitbake_var("INITRD") else "")
        append = get_bitbake_var("APPEND")

        cfg  = "UI menu.c32\n"
        cfg += "\n"
        cfg += "PROMPT " + str(prompt or 0) + "\n"
        cfg += "TIMEOUT " + str(timeout or 50) + "\n"
        cfg += "\n"
        cfg += "ALLOWOPTIONS " + str(allow_options or 1) + "\n"
        cfg += "SERIAL " + str(serial or "0 38400") + "\n"
        cfg += "DEFAULT rootfs1\n"
        cfg += "\n"
        cfg += "LABEL rootfs1\n"
        cfg += "    KERNEL /vmlinuz\n"
        cfg += "    APPEND label=rootfs1 rootwait root=LABEL=rootfs1"
        cfg += " %s" % (serial_tty or "console=ttyS0,38400n8")
        cfg += " " + initrd
        cfg += "\n"
        cfg += "LABEL rootfs2\n"
        cfg += "    KERNEL /vmlinuz\n"
        cfg += "    APPEND label=rootfs2 rootwait root=LABEL=rootfs2"
        cfg += " %s" % (serial_tty or "console=ttyS0,38400n8")
        cfg += " " + initrd
        cfg += "\n"

        return cfg

    @classmethod
    def do_configure_partition(cls, part, source_params, creator, cr_workdir,
                               oe_builddir, bootimg_dir, kernel_dir,
                               native_sysroot):
        """
        Called before do_prepare_partition(), creates syslinux config
        """
        hdddir = "%s/hdd/boot" % cr_workdir

        install_cmd = "install -d %s" % hdddir
        exec_cmd(install_cmd)

        cfg = cls._syslinux_config(creator.ks.bootloader)

        logger.debug("Writing syslinux config %s/hdd/boot/syslinux.cfg",
                     cr_workdir)

        f = open("%s/hdd/boot/syslinux.cfg" % cr_workdir, "w")
        f.write(cfg)
        f.close()

    @classmethod
    def do_prepare_partition(cls, part, source_params, creator, cr_workdir,
                             oe_builddir, bootimg_dir, kernel_dir,
                             rootfs_dir, native_sysroot):
        """
        Called to do the actual content population for a partition i.e. it
        'prepares' the partition to be incorporated into the image.
        In this case, prepare content for legacy bios boot partition.
        """
        bootimg_dir = cls._get_bootimg_dir(bootimg_dir, 'syslinux')

        staging_kernel_dir = kernel_dir

        hdddir = "%s/hdd/boot" % cr_workdir

        cmds = ("install -m 0644 %s/bzImage %s/vmlinuz" %
                (staging_kernel_dir, hdddir),
                "install -m 444 %s/syslinux/ldlinux.sys %s/ldlinux.sys" %
                (bootimg_dir, hdddir),
                "install -m 0644 %s/syslinux/menu.c32 %s/menu.c32" %
                (bootimg_dir, hdddir),
                "install -m 444 %s/syslinux/libcom32.c32 %s/libcom32.c32" %
                (bootimg_dir, hdddir),
                "install -m 444 %s/syslinux/libutil.c32 %s/libutil.c32" %
                (bootimg_dir, hdddir))
        
        initrd = get_bitbake_var("INITRD")
        if initrd:
            cmds += (("install -m 0644 %s %s/initrd" % (initrd, hdddir)), )

        for install_cmd in cmds:
            exec_cmd(install_cmd)

        du_cmd = "du -bks %s" % hdddir
        out = exec_cmd(du_cmd)
        blocks = int(out.split()[0])

        extra_blocks = part.get_extra_block_count(blocks)

        if extra_blocks < BOOTDD_EXTRA_SPACE:
            extra_blocks = BOOTDD_EXTRA_SPACE

        blocks += extra_blocks

        logger.debug("Added %d extra blocks to %s to get to %d total blocks",
                     extra_blocks, part.mountpoint, blocks)

        # dosfs image, created by mkdosfs
        bootimg = "%s/boot%s.img" % (cr_workdir, part.lineno)

        dosfs_cmd = "mkdosfs -n boot -S 512 -C %s %d" % (bootimg, blocks)
        exec_native_cmd(dosfs_cmd, native_sysroot)

        mcopy_cmd = "mcopy -i %s -s %s/* ::/" % (bootimg, hdddir)
        exec_native_cmd(mcopy_cmd, native_sysroot)

        syslinux_cmd = "syslinux %s" % bootimg
        exec_native_cmd(syslinux_cmd, native_sysroot)

        chmod_cmd = "chmod 644 %s" % bootimg
        exec_cmd(chmod_cmd)

        du_cmd = "du -Lbks %s" % bootimg
        out = exec_cmd(du_cmd)
        bootimg_size = out.split()[0]

        part.size = int(bootimg_size)
        part.source_file = bootimg
