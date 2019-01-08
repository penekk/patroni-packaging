%define        ENVNAME  patroni
%define        INSTALLPATH /opt/app/patroni
%define debug_package %{nil}
Name:          patroni
Version:       1.5.3
Release:       1.rhel7
License:       MIT
Summary:       PostgreSQL high-availability manager
Source:        patroni-1.5.3.tar.gz
Source1:       patroni-customizations.tar.gz
Patch0:        service-info-only-in-pretty-format.patch
Patch1:        patronictl-reinit-wait.patch
BuildRoot:     %{_tmppath}/%{buildprefix}-buildroot
Requires:      /usr/bin/python2.7, python-psycopg2 >= 2.6.1, postgresql-server, libyaml
BuildRequires: prelink libyaml-devel gcc
Requires(post): %{_sbindir}/update-alternatives
Requires(postun):       %{_sbindir}/update-alternatives

%description
Packaged version of Patroni HA manager.

%prep
%setup
%setup -D -T -a 1
%patch0 -p1
%patch1 -p1

%build
# remove some things
#rm -f $RPM_BUILD_ROOT/%{prefix}/*.spec

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT%{INSTALLPATH}
virtualenv --distribute $RPM_BUILD_ROOT%{INSTALLPATH}
grep -v psycopg2 requirements.txt | sed 's/kubernetes=.*/kubernetes/' > requirements-venv.txt
$RPM_BUILD_ROOT%{INSTALLPATH}/bin/pip install -U setuptools
$RPM_BUILD_ROOT%{INSTALLPATH}/bin/pip install -r requirements-venv.txt
$RPM_BUILD_ROOT%{INSTALLPATH}/bin/pip install --no-deps .
rm $RPM_BUILD_ROOT%{INSTALLPATH}/lib/python2.7/site-packages/consul/aio.py

rm -rf $RPM_BUILD_ROOT/usr/

virtualenv --relocatable $RPM_BUILD_ROOT%{INSTALLPATH}
sed -i "s#$RPM_BUILD_ROOT##" $RPM_BUILD_ROOT%{INSTALLPATH}/bin/activate*

#find $(VENV_PATH) -name \*py[co] -exec rm {} \;
#find $(VENV_PATH) -name no-global-site-packages.txt -exec rm {} \;
cp -r extras/ $RPM_BUILD_ROOT%{INSTALLPATH}

mkdir -p $RPM_BUILD_ROOT/lib/systemd/system/
cp patroni.2.service $RPM_BUILD_ROOT/lib/systemd/system/patroni.service
cp patroni-watchdog.service $RPM_BUILD_ROOT/lib/systemd/system/patroni-watchdog.service

mkdir -p $RPM_BUILD_ROOT%{INSTALLPATH}/etc/
cp postgres-telia.yml $RPM_BUILD_ROOT%{INSTALLPATH}/etc/postgresql.yml.sample
chmod 0600 $RPM_BUILD_ROOT%{INSTALLPATH}/etc/postgresql.yml.sample

# undo prelinking
find $RPM_BUILD_ROOT%{INSTALLPATH}/bin/ -type f -perm /u+x,g+x -exec /usr/sbin/prelink -u {} \;
# Remove debug info containing BUILDROOT. Hopefully nobody needs to debug or profile the python modules
find $RPM_BUILD_ROOT%{INSTALLPATH}/lib/ -type f -name '*.so' -exec /usr/bin/strip -g {} \;


%post
%{_sbindir}/update-alternatives --install %{_bindir}/patroni \
  patroni %{INSTALLPATH}/bin/patroni 10 \
  --slave %{_bindir}/patronictl patroni-patronictl %{INSTALLPATH}/bin/patronictl

%postun
if [ $1 -eq 0 ] ; then
  %{_sbindir}/update-alternatives --remove patroni %{INSTALLPATH}/bin/patroni
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/opt/app/patroni
%attr(-, postgres, postgres) /opt/app/patroni/etc
%attr(664, root, root) /lib/systemd/system/patroni.service
%attr(664, root, root) /lib/systemd/system/patroni-watchdog.service

%changelog
* Tue Jan 8 2019 Andrzej Penkowski 1.5.3-1.rhel7
- Update to 1.5.3
- patronictl-reinit-wait.patch touchup following changes in
  https://github.com/zalando/patroni/pull/823/commits/cf70a44a13b10ceab95941ff991f3545dbd6425d

* Fri Sep 21 2018 Ants Aasma 1.5.0-1.rhel7
- Update to 1.5.0

* Wed May 23 2018 Ants Aasma 1.4.4-1.rhel7
- Update to 1.4.4
- Add patronictl reinit --wait feature

* Thu May 10 2018 Ants Aasma 1.4.3-2.rhel7
- Only display service info output in pretty format.

* Tue May 8 2018 Ants Aasma  1.4.3-1.rhel7
- Update to 1.4.3

* Fri Dec 8 2017 Ants Aasma  1.3.6-1.rhel7
- Update to 1.3.6

* Sat Sep 30 2017 Ants Aasma  1.3.4-2.rhel7
- Add warning for cluster being in paused mode
- Pull in master changes up to cfdda23e

