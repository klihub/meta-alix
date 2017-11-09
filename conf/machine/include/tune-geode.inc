# Machine tuning settings for the Geode LX x86-compatible CPU architecure.

DEFAULTTUNE ?= "geode"

require conf/machine/include/x86/arch-x86.inc

# Extra tune features
#
# According to Net folklore (mostly http://wiki.laptop.org/go/Geode and
# https://gcc.gnu.org/bugzilla/show_bug.cgi?id=41989), the gcc 'geode'
# march and mtune settings are actually meant/optimised for the Geode LX,
# so we go'll with that... A suggested good enough alternative for gcc
# would be "-Os -mcpu=pentiumpro -mtune=generic".

TUNEVALID[geode] = "Enable Geode LX specific processor optimizations"
TUNE_CCARGS .= "${@bb.utils.contains('TUNE_FEATURES', 'geode', ' -march=geode', '', d)}"

# Extra tune selections
AVAILTUNES += "geode"
TUNE_FEATURES_tune-geode = "${TUNE_FEATURES_tune-x86} geode"
BASE_LIB_tune-geode = "lib"
TUNE_PKGARCH_tune-geode = "geode"
PACKAGE_EXTRA_ARCHS_tune-geode = "${PACKAGE_EXTRA_ARCHS_tune-x86} geode"
