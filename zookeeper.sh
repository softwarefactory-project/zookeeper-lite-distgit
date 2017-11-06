#!/bin/sh

exec /usr/bin/java -Xmx${ZK_HEAP_LIMIT} \
    -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.local.only=false \
    -Dlog4j.configuration=file:///etc/zookeeper/log4j.properties \
    org.apache.zookeeper.server.quorum.QuorumPeerMain /etc/zookeeper/zoo.cfg
