Name:          zookeeper-lite
Version:       3.4.10
Release:       2%{?dist}
Summary:       A lite version of the zookeeper service, without the clients, bindings or netty.
License:       ASL 2.0 and BSD
URL:           https://zookeeper.apache.org/
Source0:       https://www.apache.org/dist/zookeeper/zookeeper-%{version}/zookeeper-%{version}.tar.gz
Source1:       zookeeper.service
Source2:       pom.template

BuildRequires: ant
BuildRequires: systemd
BuildRequires: log4j
BuildRequires: jline
BuildRequires: slf4j

Requires:      java-1.8.0-openjdk
Requires:      log4j
Requires:      jline
Requires:      slf4j
Requires:      wait4service

Provides:      zookeeper


%description
ZooKeeper is a centralized service for maintaining configuration information,
naming, providing distributed synchronization, and providing group services.


%prep
%autosetup -n zookeeper-%{version}

# Remove bundled stuff
find -name "*.jar" -o -name "*.class" -delete

# Disable netty
rm ./src/java/main/org/apache/zookeeper/server/NettyServerCnxn*

# Disable Log4jMBeans, otherwise build fails with:
# [javac] src/java/main/org/apache/zookeeper/jmx/ManagedUtil.java:61: error: cannot find symbol
# [javac]     LoggerRepository r = LogManager.getLoggerRepository();
cat <<EOF> src/java/main/org/apache/zookeeper/jmx/ManagedUtil.java
package org.apache.zookeeper.jmx;
import javax.management.JMException;
public class ManagedUtil {
    public static void registerLog4jMBeans() throws JMException { return; }
}
EOF

# Remove ivy task
sed -i 's|depends="ivy-retrieve,|depends="|' build.xml

# Fix missing hostname
sed -i 's|<exec executable="hostname" outputproperty="host.name"/>|<!--exec executable="hostname" outputproperty="host.name"/-->|' build.xml
sed -i 's|<attribute name="Built-On" value="${host.name}" />|<attribute name="Built-On" value="${user.name}" />|' build.xml

# Force the use of local libraries
sed -i 's|<path id="java.classpath">|<path id="java.classpath"><fileset dir="/usr/share/java"><include name="*.jar" /></fileset>|' build.xml
sed -i 's|<path id="java.classpath">|<path id="java.classpath"><fileset dir="/usr/share/java/slf4j"><include name="*.jar" /></fileset>|' build.xml

# Fix datadir
sed -i 's|dataDir=/tmp/zookeeper|dataDir=/var/lib/zookeeper|' conf/zoo_sample.cfg

# Add missing pom
cp %{SOURCE2} src/


%build
%ant jar


%install
install -p -D -m 644 build/zookeeper-%{version}.jar %{buildroot}%{_javadir}/zookeeper.jar

install -d -m 755 %{buildroot}%{_sysconfdir}/zookeeper
install -p -D -m 644 conf/configuration.xsl conf/log4j.properties %{buildroot}%{_sysconfdir}/zookeeper
install -p -D -m 644 conf/zoo_sample.cfg %{buildroot}%{_sysconfdir}/zookeeper/zoo.cfg

install -p -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/zookeeper.service

install -d -m 755 %{buildroot}%{_sysconfdir}/sysconfig/
echo "CLASSPATH=$(build-classpath jline log4j):/usr/share/java/slf4j/slf4j-api.jar:/usr/share/java/slf4j/slf4j-log4j12.jar:/usr/share/java/zookeeper.jar" > %{buildroot}%{_sysconfdir}/sysconfig/zookeeper
echo "ZK_HEAP_LIMIT=2g" >> %{buildroot}%{_sysconfdir}/sysconfig/zookeeper

install -d -m 750 %{buildroot}%{_localstatedir}/log/zookeeper
install -d -m 750 %{buildroot}%{_sharedstatedir}/zookeeper


%pre
getent group zookeeper > /dev/null || groupadd -r zookeeper
getent passwd zookeeper > /dev/null || useradd -r -g zookeeper \
    -d %{_sharedstatedir}/zookeeper -s /sbin/nologin \
    -c "ZooKeeper service account" zookeeper
exit 0


%post
%systemd_post zookeeper.service


%preun
%systemd_preun zookeeper.service


%postun
%systemd_postun_with_restart zookeeper.service


%files
%{_javadir}/zookeeper.jar
%{_sysconfdir}/zookeeper
%{_sysconfdir}/sysconfig/zookeeper
%{_unitdir}/zookeeper.service
%attr(0750,zookeeper,zookeeper) %dir %{_localstatedir}/log/zookeeper
%attr(0700,zookeeper,zookeeper) %dir %{_sharedstatedir}/zookeeper


%changelog
* Tue Sep 05 2017 Tristan Cacqueray <tdecacqu@redhat.com> 3.4.10-2
- Change zookeeper.service mode to 644

* Fri Jun 02 2017 Tristan Cacqueray <tdecacqu@redhat.com> 3.4.10-1
- Bump to 3.4.10 to fix CVE-2017-5637

* Mon Feb 20 2017 Tristan Cacqueray <tdecacqu@redhat.com> 3.4.9-1
- First package
