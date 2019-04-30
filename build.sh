#!/bin/bash

RPM_BUILD=$(type -p rpmbuild)
CURRENT_DIR="$(realpath `dirname "$0"`)"
BUILD_DIR="$CURRENT_DIR/build/"
PKG_NAME="scalix-monitoring-tool"
#SOURCE_ARCHIVE="$BUILD_DIR/SOURCES/scalix-monitoring-tool.tar.gz"


function build_archive() {
    local distro="$1"
    if [[ -d "$BUILD_DIR" ]] ; then
        rm -rf "$BUILD_DIR"
    fi
    local data_dir="$BUILD_DIR/SOURCES/$PKG_NAME/opt/scalix-monitoring-tool"
    mkdir -p "$data_dir"
    cp -r "$CURRENT_DIR/static" "$data_dir/static"
    cp -r "$CURRENT_DIR/alembic" "$data_dir/alembic"
    mkdir -p "$BUILD_DIR/SOURCES/$PKG_NAME/etc/opt/scalix-monitoring/"
    cp $CURRENT_DIR/*.ini "$BUILD_DIR/SOURCES/$PKG_NAME/etc/opt/scalix-monitoring/"
    cp -r "$CURRENT_DIR/requirements.txt" "$data_dir/requirements.txt"
    cp $CURRENT_DIR/*.py $data_dir/
    if [[ "$distro" == "rhel6" ]]; then
        mkdir -p "$BUILD_DIR/SOURCES/$PKG_NAME/etc/init.d"
        cp $CURRENT_DIR/dists/init.d/* "$BUILD_DIR/SOURCES/$PKG_NAME/etc/init.d"
    else
        mkdir -p "$BUILD_DIR/SOURCES/$PKG_NAME/etc/systemd/system/"
        cp $CURRENT_DIR/dists/systemd/* "$BUILD_DIR/SOURCES/$PKG_NAME/etc/systemd/system/"
        echo 'nothing for now'
    fi
    cp -r "$CURRENT_DIR/templates" "$data_dir/templates"
    cp -r "$CURRENT_DIR/webstats" "$data_dir/webstats"
    tar --exclude='__pycache__' -czvf  "$BUILD_DIR/SOURCES/$PKG_NAME.tar.gz" -C "$BUILD_DIR/SOURCES/$PKG_NAME/" .
}

function build_rpm() {
    local distro="$1"
    build_archive $distro
    mv -f "$BUILD_DIR/SOURCES/$PKG_NAME.tar.gz" "$BUILD_DIR/SOURCES/$PKG_NAME-$distro.tar.gz"
    $RPM_BUILD -ba --define "_topdir $BUILD_DIR" --define "TARGET_PLATFORM  $distro"  "$CURRENT_DIR/$PKG_NAME.spec"
    find "$BUILD_DIR/RPMS/" -name "scalix-*.rpm" -exec cp -fL {} "$CURRENT_DIR/"  \;
}

if [[ -n "$RPM_BUILD" ]]; then

    build_rpm 'rhel6'
    build_rpm 'rhel7'
else
    echo "rpm command not found . Can not build rpm file"
fi


DPKG_DEB=$(type -p dpkg-deb)
if [[ -n "$RPM_BUILD" ]]; then
    echo "not implemented"
    # build_archive 'rhel7'
    # next unpack prepared archive "$BUILD_DIR/SOURCES/$PKG_NAME.tar.gz"
    # $DPKG_DEB -b "$BUILD_DIR/SOURCES/scalix-autodiscover/" ./
else
    echo "dpkg-deb command not found . Can not build deb file"
fi
