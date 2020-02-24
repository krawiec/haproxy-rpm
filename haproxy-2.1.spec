%define haproxy_user	haproxy
%define haproxy_group	%{haproxy_user}
%define haproxy_home	%{_localstatedir}/lib/haproxy
%define haproxy_confdir	%{_sysconfdir}/haproxy
%define haproxy_datadir %{_datadir}/haproxy

%global _hardened_build 1

Name:			haproxy
Version:		2.1.2
Release:		1%{?dist}
Summary:		TCP/HTTP(S) proxy and load balancer for high availability environments

Group:			System Environment/Daemons
License:		GPL

URL:			https://www.haproxy.org/
Source0:		https://www.haproxy.org/download/2.0/src/%{name}-%{version}.tar.gz
Source1:		%{name}.service
Source2:		%{name}.logrotate
Source3:		%{name}.sysconfig
Source4:		%{name}.cfg
Source5:		%{name}-reload.sh

BuildRequires:		pcre-devel
BuildRequires:		zlib-devel
BuildRequires:		openssl-devel
BuildRequires:		systemd-units
BuildRequires:		systemd-devel

Requires:		/sbin/chkconfig, /sbin/service
Requires(pre):		shadow-utils
Requires(post):		systemd
Requires(preun):	systemd
Requires(postun):	systemd

BuildRoot:		%{_tmppath}/%{name}-%{version}-root

%description
HA-Proxy is a TCP/HTTP reverse proxy which is particularly suited for high
availability environments. Indeed, it can:
- route HTTP requests depending on statically assigned cookies
- spread the load among several servers while assuring server persistence
  through the use of HTTP cookies
- switch to backup servers in the event a main one fails
- accept connections to special ports dedicated to service monitoring
- stop accepting connections without breaking existing ones
- add/modify/delete HTTP headers both ways
- block requests matching a particular pattern

It needs very little resource. Its event-driven architecture allows it to easily
handle thousands of simultaneous connections on hundreds of instances without
risking the system's stability.

%prep
%setup -q

# We don't want any perl dependecies in this RPM:
%define __perl_requires /bin/true

%build
%{__make} %{?_smp_mflags} USE_PCRE=1 DEBUG="" ARCH=%{_target_cpu} TARGET="linux-glibc" SSL_INC=/home/rpmbuild/openssl-1.1.1c/include SSL_LIB=/home/rpmbuild/openssl-1.1.1c USE_LIBCRYPT=1 USE_LINUX_SPLICE=1 USE_LINUX_TPROXY=1 USE_OPENSSL=1 USE_PCRE=1 USE_PCRE_JIT=1 USE_ZLIB=1 USE_SYSTEMD=1 ADDINC="%{optflags}" ADDLIB="%{__global_ldflags} -lssl -ldl -lpthread" EXTRA_OBJS="contrib/prometheus-exporter/service-prometheus.o"

pushd contrib/halog
%{__make} halog OPTIMIZE="%{optflags}"
popd

pushd contrib/iprange
%{__make} iprange OPTIMIZE="%{optflags}"
popd

pushd contrib/ip6range
%{__make} ip6range OPTIMIZE="%{optflags}"
popd

%install
%{__make} install-bin DESTDIR=%{buildroot} PREFIX=%{_prefix} TARGET="linux2628"
%{__make} install-man DESTDIR=%{buildroot} PREFIX=%{_prefix}
#%{__make} install-doc DESTDIR=%{buildroot} PREFIX=%{_prefix}
#%{__make} install DESTDIR=%{buildroot} PREFIX=%{_prefix}

%{__install} -d -m 0755 %{buildroot}%{haproxy_home}
%{__install} -d -m 0755 %{buildroot}%{haproxy_datadir}
%{__install} -d -m 0755 %{buildroot}%{haproxy_confdir}
%{__install} -d -m 0755 %{buildroot}%{_bindir}

%{__install} -p -m 0755 ./contrib/halog/halog %{buildroot}%{_bindir}/halog
%{__install} -p -m 0755 ./contrib/iprange/iprange %{buildroot}%{_bindir}/iprange
%{__install} -p -m 0755 ./contrib/ip6range/ip6range %{buildroot}%{_bindir}/ip6range

%{__install} -p -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
%{__install} -p -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}
%{__install} -p -D -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/sysconfig/%{name}
%{__install} -p -D -m 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/%{name}/%{name}.cfg
%{__install} -p -D -m 0755 %{SOURCE5} %{buildroot}%{_bindir}/haproxy-reload

%clean
[ "%{buildroot}" != "/" ] && %{__rm} -rf %{buildroot}

%pre
getent group %{haproxy_group} >/dev/null || groupadd -f -g 188 -r %{haproxy_group}
if ! getent passwd %{haproxy_user} >/dev/null ; then
    if ! getent passwd 188 >/dev/null ; then
	useradd -r -u 188 -g %{haproxy_group} -d %{haproxy_home} -s /sbin/nologin -c "haproxy" %{haproxy_user}
    else
	useradd -r -g %{haproxy_group} -d %{haproxy_home} -s /sbin/nologin -c "haproxy" %{haproxy_user}
    fi
fi

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%defattr(-,root,root)
%attr(-,%{haproxy_user},%{haproxy_group}) %dir %{haproxy_home}
%license LICENSE
%doc CHANGELOG README ROADMAP VERSION
%doc doc/*.txt
%doc %{_mandir}/man1/%{name}.1.gz
%attr(0644,root,root) %{_unitdir}/%{name}.service
%attr(0755,root,root) %{_sbindir}/%{name}
%attr(0755,root,root) %{_bindir}/halog
%attr(0755,root,root) %{_bindir}/iprange
%attr(0755,root,root) %{_bindir}/ip6range
%attr(0755,root,root) %{haproxy_confdir}
%attr(0755,root,root) %{_bindir}/haproxy-reload
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.cfg

%changelog
* Mon Feb 10 2020 Piotr Krawiecki <Piotr.Krawiecki@pracuj.pl>
- HaProxy version 2.1.2
