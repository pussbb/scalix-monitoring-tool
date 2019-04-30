%define _target_platform %{TARGET_PLATFORM}

Name:       scalix-monitoring-tool
Version:    0.0.1
Release:    1%{?dist}.%{TARGET_PLATFORM}
Summary:    Scalix Monitoring Tool
License:    Copyright 2019 Scalix, Inc. (www.scalix.com)
Source:     %{name}-%{TARGET_PLATFORM}.tar.gz
BuildArch:  noarch
Group:      Applications/Communications
Vendor:     Scalix Corporation
URL:        http://www.scalix.com
Packager:   Scalix Support <support@scalix.com>
Requires:   python >= 3.6
%if %{TARGET_PLATFORM} == "rhel7"
BuildRequires: systemd-rpm-macros
%{?systemd_requires}
%endif


%description
Scalix Monitoring Tool.

%prep
%setup -q -c %{name}

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
cp -f --archive * %{buildroot}

%post
%if %{TARGET_PLATFORM} != "rhel6"
    %systemd_post apache-httpd.service
%endif


%postun
%if %{TARGET_PLATFORM} != "rhel6"
    %systemd_postun_with_restart apache-httpd.service
%endif

%preun
%if %{TARGET_PLATFORM} != "rhel6"
    %systemd_preun apache-httpd.service
%endif

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%if %{TARGET_PLATFORM} == "rhel6"
    /etc/init.d/*
%else
    /etc/systemd/system/*
%endif

%dir %attr(0755, nobody, nobody) /opt/scalix-monitoring-tool/static
%attr(0755, nobody, nobody) /opt/scalix-monitoring-tool/static/*

%dir %attr(0755, nobody, nobody) /opt/scalix-monitoring-tool/templates
%attr(0755, nobody, nobody) /opt/scalix-monitoring-tool/templates/*

%dir /opt/scalix-monitoring-tool/alembic
/opt/scalix-monitoring-tool/alembic/*

%dir /opt/scalix-monitoring-tool/webstats
/opt/scalix-monitoring-tool/webstats/*

%config(noreplace) /etc/opt/scalix-monitoring/alembic.ini
%config(noreplace) /etc/opt/scalix-monitoring/sxmonitoring.ini
/opt/scalix-monitoring-tool/*.py
/opt/scalix-monitoring-tool/*.txt


%changelog
