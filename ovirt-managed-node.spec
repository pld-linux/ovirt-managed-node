Summary:	The managed node daemons/scripts for oVirt
Name:		ovirt-managed-node
Version:	0.92
Release:	0.1
Source0:	%{name}-%{version}.tar.gz
# Source0-md5:	41efded0be1483b4423d80f534f70942
License:	GPL
Group:		Applications/System
URL:		http://www.ovirt.org/
BuildRequires:	dbus-devel
BuildRequires:	hal-devel
BuildRequires:	libvirt-devel
Requires(post):	/sbin/chkconfig
Requires(preun):	/sbin/chkconfig
Requires:	hal
Requires:	libvirt
ExclusiveArch:	%{ix86} %{x8664}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define app_root %{_datadir}/%{name}

%description
Provides a series of daemons and support utilities to allow an oVirt
managed node to interact with the oVirt server.

%prep
%setup -q

%build
%{__make}

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_sbindir}
install -d $RPM_BUILD_ROOT%{_sysconfdir}
install -d $RPM_BUILD_ROOT%{_sysconfdir}/chkconfig.d
install -d $RPM_BUILD_ROOT/etc/rc.d/init.d
install -d $RPM_BUILD_ROOT%{app_root}
install -d $RPM_BUILD_ROOT%{_sysconfdir}/cron.hourly
install -d $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d

install -p scripts/ovirt-awake $RPM_BUILD_ROOT%{_sbindir}
install -p ovirt-identify-node $RPM_BUILD_ROOT%{_sbindir}

install -p scripts/ovirt-functions $RPM_BUILD_ROOT/etc/rc.d/init.d
install -p scripts/ovirt-early $RPM_BUILD_ROOT/etc/rc.d/init.d
install -p scripts/ovirt $RPM_BUILD_ROOT/etc/rc.d/init.d
install -p scripts/ovirt-post $RPM_BUILD_ROOT/etc/rc.d/init.d

install -p scripts/collectd $RPM_BUILD_ROOT%{_sysconfdir}/chkconfig.d
install -p scripts/collectd.conf.in $RPM_BUILD_ROOT%{_sysconfdir}
install -p scripts/kvm-ifup $RPM_BUILD_ROOT%{_sysconfdir}
install -p scripts/dhclient-exit-hooks $RPM_BUILD_ROOT%{_sysconfdir}

install -p logrotate/ovirt-logrotate $RPM_BUILD_ROOT%{_sysconfdir}/cron.hourly
install -p logrotate/ovirt-logrotate.conf $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d

echo "oVirt Managed Node release %{version}-%{release}" > $RPM_BUILD_ROOT%{_sysconfdir}/ovirt-release

%clean
rm -rf $RPM_BUILD_ROOT

%post
/sbin/chkconfig --add ovirt-early
/sbin/chkconfig --add ovirt
/sbin/chkconfig --add ovirt-post
/sbin/chkconfig --add collectd

# just to get a boot warning to shut up
touch /etc/resolv.conf

# make libvirtd listen on the external interfaces
sed -i -e "s/^#\(LIBVIRTD_ARGS=\"--listen\"\).*/\1/" /etc/sysconfig/libvirtd

# set up qemu daemon to allow outside VNC connections
sed -i -e "s/^[[:space:]]*#[[:space:]]*\(vnc_listen = \"0.0.0.0\"\).*/\1/" %{_sysconfdir}/libvirt/qemu.conf

# set up libvirtd to listen on TCP (for kerberos)
sed -i -e "s/^[[:space:]]*#[[:space:]]*\(listen_tcp\)\>.*/\1 = 1/" \
    -e "s/^[[:space:]]*#[[:space:]]*\(listen_tls\)\>.*/\1 = 0/" \
	%{_sysconfdir}/libvirt/libvirtd.conf

# make sure we don't autostart virbr0 on libvirtd startup
rm -f %{_sysconfdir}/libvirt/qemu/networks/autostart/default.xml

# with the new libvirt (0.4.0), make sure we we setup gssapi in the mech_list
if [ `egrep -c "^mech_list: gssapi" /etc/sasl2/libvirt.conf` -eq 0 ]; then
	%{__sed} -i -e "s/^\([[:space:]]*mech_list.*\)/#\1/" /etc/sasl2/libvirt.conf
	echo "mech_list: gssapi" >> /etc/sasl2/libvirt.conf
fi

# remove the %{_sysconfdir}/krb5.conf file; it will be fetched on bootup
rm -f %{_sysconfdir}/krb5.conf

g=$(printf '\33[1m\33[32m')    # similar to g=$(tput bold; tput setaf 2)
n=$(printf '\33[m')            # similar to n=$(tput sgr0)
cat <<EOF > /etc/issue

           888     888 ${g}d8b$n         888
           888     888 ${g}Y8P$n         888
           888     888             888
   .d88b.  Y88b   d88P 888 888d888 888888
  d88''88b  Y88b d88P  888 888P'   888
  888  888   Y88o88P   888 888     888
  Y88..88P    Y888P    888 888     Y88b.
   'Y88P'      Y8P     888 888      'Y888

  Managed Node release %{version}-%{release}

  Virtualization just got the ${g}Green Light$n

EOF
cp -pf /etc/issue{,.net}

%preun
if [ "$1" = 0 ] ; then
	/sbin/chkconfig --del ovirt-early
	/sbin/chkconfig --del ovirt
	/sbin/chkconfig --del ovirt-post
fi

%files
%defattr(644,root,root,755)
%doc README NEWS AUTHOR ChangeLog
%attr(755,root,root) %{_sbindir}/ovirt-awake
%attr(755,root,root) %{_sbindir}/ovirt-identify-node
%attr(754,root,root) /etc/rc.d/init.d/ovirt-early
%attr(754,root,root) /etc/rc.d/init.d/ovirt
%attr(754,root,root) /etc/rc.d/init.d/ovirt-post
/etc/rc.d/init.d/ovirt-functions
%{_sysconfdir}/kvm-ifup
%{_sysconfdir}/dhclient-exit-hooks
%{_sysconfdir}/collectd.conf.in
%{_sysconfdir}/chkconfig.d/collectd
%config(noreplace) %verify(not md5 mtime size) /etc/logrotate.d/ovirt-logrotate.conf
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/cron.hourly/ovirt-logrotate
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/ovirt-release
