#!/bin/sh

GRADLE_APP_NAME=Gradle
APP_BASE_NAME=`basename "$0"`
GRADLE_USER_HOME=${GRADLE_USER_HOME:-$HOME/.gradle}

exec "$GRADLE_USER_HOME/wrapper/dists/gradle-8.0-bin/*/gradle-8.0/bin/gradle" "$@"
