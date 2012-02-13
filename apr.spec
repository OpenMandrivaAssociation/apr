%if %mandriva_branch == Cooker
# Cooker
%define release %mkrel 0.1
%else
# Old distros
%define subrel 1
%define release %mkrel 0
%endif

%define aprver 1
%define libname %mklibname apr %{aprver}
%define develname %mklibname -d apr
%define epoch 1

Summary:	Apache Portable Runtime library
Name:		apr
Version:	1.4.6
Release:	%release
License:	Apache License
Group:		System/Libraries
URL:		http://apr.apache.org/
Source0:	http://www.apache.org/dist/apr/apr-%{version}.tar.gz
Source1:	http://www.apache.org/dist/apr/apr-%{version}.tar.gz.asc
Patch0:		apr-0.9.3-deplibs.patch
Patch1:		apr-1.1.0-config.diff
Patch2:		apr-1.0.0-mutextype_reorder.diff
Patch4:		apr-1.2.2-locktimeout.patch
BuildRequires:	autoconf automake libtool
BuildRequires:	doxygen
BuildRequires:	python
%if %mdkversion >= 201000
BuildRequires: libuuid-devel
%else
BuildRequires:	e2fsprogs-devel
%endif
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
The mission of the Apache Portable Runtime (APR) is to provide a free library
of C data structures and routines, forming a system portability layer to as
many operating systems as possible, including Unices, MS Win32, BeOS and OS/2.

%package -n	%{libname}
Summary:	Apache Portable Runtime library
Group: 		System/Libraries
Provides:	lib%{name} = %{epoch}:%{version}-%{release}
Obsoletes:	lib%{name}
Epoch:		%{epoch}

%description -n	%{libname}
The mission of the Apache Portable Runtime (APR) is to provide a free library
of C data structures and routines, forming a system portability layer to as
many operating systems as possible, including Unices, MS Win32, BeOS and OS/2.

%package -n	%{develname}
Summary:	APR library development kit
Group:		Development/C
Requires:	%{libname} = %{epoch}:%{version}
Requires:	libtool
Provides:	%{mklibname apr -d 1} = %{epoch}:%{version}-%{release}
Obsoletes:	%{mklibname apr -d 1}
Provides:	%{name}-devel = %{epoch}:%{version}-%{release}
Obsoletes:	%{name}-devel
Epoch:		%{epoch}

%description -n	%{develname}
This package provides the support files which can be used to build applications
using the APR library. The mission of the Apache Portable Runtime (APR) is to
provide a free library of C data structures and routines.

%prep

%setup -q -n %{name}-%{version}
%patch0 -p0 -b .deplibs
%patch1 -p0 -b .config
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
    includedir:    %{_includedir}/apr-%{aprver}
    sysconfdir:    %{_sysconfdir}
    datadir:       %{_datadir}
    installbuilddir: %{_libdir}/apr-%{aprver}/build
    localstatedir: /var
    runtimedir:    /var/run
    libsuffix:     -\${APR_MAJOR_VERSION}
</Layout>
EOF

%build
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
    --includedir=%{_includedir}/apr-%{aprver} \
    --with-installbuilddir=%{_libdir}/apr-%{aprver}/build \
    --enable-layout=NUX \
%ifarch %ix86
%ifnarch i386 i486
    --enable-nonportable-atomics=yes \
%endif
%endif
    --enable-lfs \
    --enable-threads \
    --with-sendfile  \
    --with-devrandom=/dev/urandom

%make
make dox

%check
make check

%install
rm -rf %{buildroot}

%makeinstall_std

# These are referenced by apr_rules.mk
for f in make_exports.awk make_var_export.awk; do
    install -m0644 build/${f} %{buildroot}%{_libdir}/apr-%{aprver}/build/${f}
done

install -m0755 build/mkdir.sh %{buildroot}%{_libdir}/apr-%{aprver}/build/mkdir.sh

# these are needed if apr-util is ./buildconf'ed
for f in apr_common.m4 apr_hints.m4 apr_network.m4 apr_threads.m4 find_apr.m4; do
    install -m0644 build/${f} %{buildroot}%{_libdir}/apr-%{aprver}/build/${f}
done
install -m0755 build/gen-build.py %{buildroot}%{_libdir}/apr-%{aprver}/build/

# enforce system libtool
ln -snf %{_bindir}/libtool %{buildroot}%{_libdir}/apr-%{aprver}/build/libtool

# Sanitize apr_rules.mk
sed -e "/^apr_build/d" \
    -e 's|$(apr_builders)|%{_libdir}/apr-%{aprver}/build|g' \
    -e 's|$(apr_builddir)|%{_libdir}/apr-%{aprver}/build|g' \
    < build/apr_rules.mk > %{buildroot}%{_libdir}/apr-%{aprver}/build/apr_rules.mk

# antibork
perl -pi -e "s|^top_builddir=.*|top_builddir=%{_libdir}/apr-%{aprver}/build|g" %{buildroot}%{_libdir}/apr-%{aprver}/build/apr_rules.mk

# Move docs to more convenient location
rm -rf html
cp -r docs/dox/html html

# here too
perl -pi -e "s|-luuid -lcrypt||g" \
    %{buildroot}%{_bindir}/apr-%{aprver}-config \
    %{buildroot}%{_libdir}/pkgconfig/*.pc

# Unpackaged files:
rm -f %{buildroot}%{_libdir}/apr.exp

# extra headers
install -d %{buildroot}%{_includedir}/apr-%{aprver}/arch/unix
install -m0644 include/arch/apr_private_common.h %{buildroot}%{_includedir}/apr-%{aprver}/arch/
install -m0644 include/arch/unix/*.h %{buildroot}%{_includedir}/apr-%{aprver}/arch/unix/

# cleanup
rm -f %{buildroot}%{_libdir}/libapr*.*a

%clean
rm -rf %{buildroot}

%files -n %{libname}
%defattr(-,root,root,-)
%doc CHANGES README*
%{_libdir}/libapr-%{aprver}.so.*

%files -n %{develname}
%defattr(-,root,root,-)
%doc docs/APRDesign.html docs/canonical_filenames.html
%doc docs/incomplete_types docs/non_apr_programs
%doc --parents html
%{_bindir}/apr-%{aprver}-config
%{_libdir}/libapr-%{aprver}.so
%dir %{_libdir}/apr-%{aprver}
%dir %{_libdir}/apr-%{aprver}/build
%{_libdir}/apr-%{aprver}/build/*
%{_libdir}/pkgconfig/*.pc
%dir %{_includedir}/apr-%{aprver}
%dir %{_includedir}/apr-%{aprver}/arch
%dir %{_includedir}/apr-%{aprver}/arch/unix
%{_includedir}/apr-%{aprver}/*.h
%{_includedir}/apr-%{aprver}/arch/*.h
%{_includedir}/apr-%{aprver}/arch/unix/*.h
