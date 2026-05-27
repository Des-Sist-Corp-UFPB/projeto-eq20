#!/bin/sh
set -e

MAVEN_WRAPPER_VERSION=0.5.6
MVN_CMD="mvn"

if [ ! -f ".mvn/wrapper/maven-wrapper.jar" ]; then
  echo "Downloading Maven Wrapper..."
  mkdir -p .mvn/wrapper
  curl -o .mvn/wrapper/maven-wrapper.jar https://repo.maven.apache.org/maven2/org/apache/maven/wrapper/maven-wrapper/${MAVEN_WRAPPER_VERSION}/maven-wrapper-${MAVEN_WRAPPER_VERSION}.jar
fi

exec "$MVN_CMD" "$@"