FILESEXTRAPATHS_prepend := "${THISDIR}/files:"

PR := "${PR}.1"

COMPATIBLE_MACHINE_alix = "alix"
KBRANCH_alix = "v5.4/standard/base"

SRC_URI += " \
    file://defconfig \
"

# replace these SRCREVs with the real commit ids once you've had
# the appropriate changes committed to the upstream linux-yocto repo
SRCREV_machine_pn-linux-yocto_alix ?= "${AUTOREV}"
SRCREV_meta_pn-linux-yocto_alix ?= "${AUTOREV}"

#LINUX_VERSION = "4.10"
#Remove the following line once AUTOREV is locked to a certain SRCREV
KERNEL_VERSION_SANITY_SKIP = "1"
