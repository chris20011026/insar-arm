# Bash/zsh compatible. Conda owns activation; settings are scoped to this prefix.
export _INSAR_ARM_HAD_ISCE_HOME="${ISCE_HOME+yes}"
export _INSAR_ARM_PREV_ISCE_HOME="${ISCE_HOME-}"
export _INSAR_ARM_HAD_ISCE_STACK="${ISCE_STACK+yes}"
export _INSAR_ARM_PREV_ISCE_STACK="${ISCE_STACK-}"
export _INSAR_ARM_HAD_PYTHONPATH="${PYTHONPATH+yes}"
export _INSAR_ARM_PREV_PYTHONPATH="${PYTHONPATH-}"
export _INSAR_ARM_HAD_PYTHONHOME="${PYTHONHOME+yes}"
export _INSAR_ARM_PREV_PYTHONHOME="${PYTHONHOME-}"
export _INSAR_ARM_HAD_CONDA_SUBDIR="${CONDA_SUBDIR+yes}"
export _INSAR_ARM_PREV_CONDA_SUBDIR="${CONDA_SUBDIR-}"
export _INSAR_ARM_HAD_MAGICK_CONFIGURE_PATH="${MAGICK_CONFIGURE_PATH+yes}"
export _INSAR_ARM_PREV_MAGICK_CONFIGURE_PATH="${MAGICK_CONFIGURE_PATH-}"
export _INSAR_ARM_ROOT="$CONDA_PREFIX"
export ISCE_HOME="$CONDA_PREFIX/lib/python3.12/site-packages/isce"
export ISCE_STACK="$CONDA_PREFIX/share/isce2"
# The stack ROOT is needed for imports such as topsStack.Stack.
export PYTHONPATH="$ISCE_HOME:$ISCE_HOME/applications:$ISCE_HOME/components:$ISCE_HOME/library:$ISCE_STACK"
unset PYTHONHOME
export CONDA_SUBDIR=osx-arm64
export MAGICK_CONFIGURE_PATH="$CONDA_PREFIX/etc/insar-arm-imagemagick"

_insar_arm_clean_paths() {
    local remaining="$PATH" entry cleaned="" first=1 more
    while :; do
        more=0
        case "$remaining" in
            *:*) entry="${remaining%%:*}"; remaining="${remaining#*:}"; more=1 ;;
            *) entry="$remaining" ;;
        esac
        case "$entry" in
            "$_INSAR_ARM_ROOT/bin"|"$_INSAR_ARM_ROOT/lib/python3.12/site-packages/isce/applications"|"$_INSAR_ARM_ROOT/share/isce2/alosStack"|"$_INSAR_ARM_ROOT/share/isce2/stripmapStack"|"$_INSAR_ARM_ROOT/share/isce2/topsStack") ;;
            *) if [ "$first" = 1 ]; then cleaned="$entry"; first=0; else cleaned="$cleaned:$entry"; fi ;;
        esac
        [ "$more" = 1 ] || break
    done
    export PATH="$cleaned"
}
_insar_arm_use_stack() {
    _insar_arm_clean_paths
    # Stack-specific names (e.g. geocode.py) must win over MintPy's names.
    export PATH="$ISCE_STACK/$1:$CONDA_PREFIX/bin:$ISCE_HOME/applications:$PATH"
    printf 'Using %s (ARM)\n' "$1"
}
use_alosStack() { _insar_arm_use_stack alosStack; }
use_topsStack() { _insar_arm_use_stack topsStack; }
use_stripmapStack() { _insar_arm_use_stack stripmapStack; }
use_mintpy() {
    _insar_arm_clean_paths
    export PATH="$CONDA_PREFIX/bin:$ISCE_HOME/applications:$PATH"
    printf 'Using MintPy tools (ARM)\n'
}
_insar_arm_clean_paths
export PATH="$CONDA_PREFIX/bin:$ISCE_HOME/applications:$PATH"
