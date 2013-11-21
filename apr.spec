%define api	1
%define major	0
%define libname %mklibname apr %{api} %{major}
%define devname %mklibname -d apr
%bcond_with	crosscompile

Summary:	Apache Portable Runtime library
Name:		apr
Epoch:		1
Version:	1.5.0
Release:	1
License:	Apache License
Group:		System/Libraries
Url:		http://apr.apache.org/
Source0:	http://www.apache.org/dist/apr/%{name}-%{version}.tar.bz2
Source1:	http://www.apache.org/dist/apr/%{name}-%{version}.tar.bz2.asc
Patch1:		apr-1.4.6-config.diff
Patch2:		apr-1.0.0-mutextype_reorder.diff
Patch4:		apr-1.2.2-locktimeout.patch

BuildRequires:	doxygen
BuildRequires:	libtool
BuildRequires:	python
BuildRequires:	pkgconfig(uuid)

%description
The mission of the Apache Portable Runtime (APR) is to provide a free library
of C data structures and routines, forming a system portability layer to as
many operating systems as possible, including Unices, MS Win32, BeOS and OS/2.

%package -n	%{libname}
Summary:	Apache Portable Runtime library
Group: 		System/Libraries
Obsoletes:	%{_lib}apr1

%description -n	%{libname}
The mission of the Apache Portable Runtime (APR) is to provide a free library
of C data structures and routines, forming a system portability layer to as
many operating systems as possible, including Unices, MS Win32, BeOS and OS/2.

%package -n	%{devname}
Summary:	APR library development kit
Group:		Development/C
Requires:	%{libname} = %{EVRD}
Provides:	%{name}-devel = %{EVRD}

%description -n	%{devname}
This package provides the support files which can be used to build applications
using the APR library. The mission of the Apache Portable Runtime (APR) is to
provide a free library of C data structures and routines.

%prep
%setup -q
%patch1 -p1 -b .config
%patch2 -p0 -b .mutextype_reorder
%patch4 -p0 -b .locktimeout

cat >> config.layout << EOF
<Layout NUX>
    prefix:        %{_prefix}
    exec_prefix:   %{_prefix}
    bindir:        %{_bindir}
    sbindir:       %{_sbindir}
    libdir:        %{_libdir}
    libexecdir:    %{_libexecdir}
    mandir:        %{_mandir}
    infodir:       %{_infodir}
    includedir:    %{_includedir}/apr-%{api}
    sysconfdir:    %{_sysconfdir}
    datadir:       %{_datadir}
    installbuilddir: %{_libdir}/apr-%{api}/build
    localstatedir: /var
    runtimedir:    /var/run
    libsuffix:     -\${APR_MAJOR_VERSION}
</Layout>
EOF

%build
%if %{with crosscompile}
export ac_cv_file__dev_zero=yes
export ac_cv_func_setpgrp_void=yes
export apr_cv_process_shared_works=yes
export apr_cv_mutex_robust_shared=no
export apr_cv_tcp_nodelay_with_cork=yes
export ac_cv_sizeof_struct_iovec=8
export apr_cv_mutex_recursive=yes
%endif
%serverbuild

# We need to re-run ./buildconf because of any applied patch(es)
#rm -f configure; sh ./buildconf
./buildconf

# Forcibly prevent detection of shm_open (which then picks up but
# does not use -lrt).

cat >> config.cache << EOF
ac_cv_search_shm_open=no
EOF

%configure2_5x \
	--cache-file=config.cache \
	--includedir=%{_includedir}/apr-%{api} \
	--with-installbuilddir=%{_libdir}/apr-%{api}/build \
	--enable-layout=NUX \
%ifarch %ix86
%ifnarch i386 i486
	--enable-nonportable-atomics=yes \
%endif
%endif
	--enable-lfs \
	--enable-threads \
	--with-sendfile  \
	--with-devrandom=/dev/urandom \
	--disable-static

%make LIBS="-lpthread"
make dox

%check
make check

%install
%makeinstall_std

# These are referenced by apr_rules.mk
for f in make_exports.awk make_var_export.awk; do
    install -m0644 build/${f} %{buildroot}%{_libdir}/apr-%{api}/build/${f}
done

install -m0755 build/mkdir.sh %{buildroot}%{_libdir}/apr-%{api}/build/mkdir.sh

# these are needed if apr-util is ./buildconf'ed
for f in apr_common.m4 apr_hints.m4 apr_network.m4 apr_threads.m4 find_apr.m4; do
    install -m0644 build/${f} %{buildroot}%{_libdir}/apr-%{api}/build/${f}
done
install -m0755 build/gen-build.py %{buildroot}%{_libdir}/apr-%{api}/build/

# enforce system libtool
ln -snf %{_bindir}/libtool %{buildroot}%{_libdir}/apr-%{api}/build/libtool

# Sanitize apr_rules.mk
sed -e "/^apr_build/d" \
    -e 's|$(apr_builders)|%{_libdir}/apr-%{api}/build|g' \
    -e 's|$(apr_builddir)|%{_libdir}/apr-%{api}/build|g' \
    < build/apr_rules.mk > %{buildroot}%{_libdir}/apr-%{api}/build/apr_rules.mk

# antibork
perl -pi -e "s|^top_builddir=.*|top_builddir=%{_libdir}/apr-%{api}/build|g" %{buildroot}%{_libdir}/apr-%{api}/build/apr_rules.mk

# Move docs to more convenient location
rm -rf html
cp -r docs/dox/html html

# here too
perl -pi -e "s|-luuid -lcrypt||g" \
    %{buildroot}%{_bindir}/apr-%{api}-config \
    %{buildroot}%{_libdir}/pkgconfig/*.pc

# Unpackaged files:
rm -f %{buildroot}%{_libdir}/apr.exp

# extra headers
install -d %{buildroot}%{_includedir}/apr-%{api}/arch/unix
install -m0644 include/arch/apr_private_common.h %{buildroot}%{_includedir}/apr-%{api}/arch/
install -m0644 include/arch/unix/*.h %{buildroot}%{_includedir}/apr-%{api}/arch/unix/

%files -n %{libname}
%{_libdir}/libapr-%{api}.so.%{major}*

%files -n %{devname}
%doc CHANGES README*
%doc docs/APRDesign.html docs/canonical_filenames.html
%doc docs/incomplete_types docs/non_apr_programs
%doc --parents html
%{_bindir}/apr-%{api}-config
%{_libdir}/libapr-%{api}.so
%dir %{_libdir}/apr-%{api}
%dir %{_libdir}/apr-%{api}/build
%{_libdir}/apr-%{api}/build/*
%{_libdir}/pkgconfig/*.pc
%dir %{_includedir}/apr-%{api}
%dir %{_includedir}/apr-%{api}/arch
%dir %{_includedir}/apr-%{api}/arch/unix
%{_includedir}/apr-%{api}/*.h
%{_includedir}/apr-%{api}/arch/*.h
%{_includedir}/apr-%{api}/arch/unix/*.h

