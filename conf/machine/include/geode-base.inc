#
# Base machine settings for a Geode (LX) X86-compatible architecture BSPs
#

#
# common settings for Geode (LX) machines
#
MACHINE_FEATURES += "pci x86 acpi"

MACHINE_EXTRA_RRECOMMENDS += "kernel-modules"

IMAGE_FSTYPES ?= "live"
NOISO ?= "1"

KERNEL_IMAGETYPE ?= "bzImage"

SERIAL_CONSOLE ?= "38400 ttyS0"

#
# kernel-related variables
#
PREFERRED_PROVIDER_virtual/kernel ??= "linux-yocto"
PREFERRED_VERSION_linux-yocto ??= "4.12%"
