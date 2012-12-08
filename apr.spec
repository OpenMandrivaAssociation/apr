%define aprver 1
%define libname %mklibname apr %{aprver}
%define develname %mklibname -d apr
%define epoch 1

Summary:	Apache Portable Runtime library
Name:		apr
Version:	1.4.6
Release:	1
License:	Apache License
Group:		System/Libraries
URL:		http://apr.apache.org/
Source0:	http://www.apache.org/dist/apr/apr-%{version}.tar.gz
Source1:	http://www.apache.org/dist/apr/apr-%{version}.tar.gz.asc
Patch0:		apr-0.9.3-deplibs.patch
Patch1:		apr-1.4.6-config.diff
Patch2:		apr-1.0.0-mutextype_reorder.diff
Patch4:		apr-1.2.2-locktimeout.patch
BuildRequires:	autoconf automake libtool
BuildRequires:	doxygen
BuildRequires:	python
BuildRequires:	pkgconfig(uuid)

%description
The mission of the Apache Portable Runtime (APR) is to provide a free library
of C data structures and routines, forming a system portability layer to as
many operating systems as possible, including Unices, MS Win32, BeOS and OS/2.

%package -n	%{libname}
Summary:	Apache Portable Runtime library
Group: 		System/Libraries
Provides:	lib%{name} = %{EVRD}
Epoch:		%{epoch}

%description -n	%{libname}
The mission of the Apache Portable Runtime (APR) is to provide a free library
of C data structures and routines, forming a system portability layer to as
many operating systems as possible, including Unices, MS Win32, BeOS and OS/2.

%package -n	%{develname}
Summary:	APR library development kit
Group:		Development/C
Requires:	%{libname} = %{EVRD}
Requires:	libtool
Provides:	%{mklibname apr -d 1} = %{EVRD}
Provides:	%{name}-devel = %{EVRD}
Epoch:		%{epoch}

%description -n	%{develname}
This package provides the support files which can be used to build applications
using the APR library. The mission of the Apache Portable Runtime (APR) is to
provide a free library of C data structures and routines.

%prep
%setup -q -n %{name}-%{version}
%patch0 -p0 -b .deplibs
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
    --with-devrandom=/dev/urandom \
    --disable-static

%make
make dox

%check
make check

%install
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

%files -n %{libname}
%doc CHANGES README*
%{_libdir}/libapr-%{aprver}.so.*

%files -n %{develname}
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


%changelog
* Tue Feb 14 2012 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.4.6-2mdv2012.0
+ Revision: 774069
- fix apr-config to print error to stderr for --apr-la-file option

* Tue Feb 14 2012 Oden Eriksson <oeriksson@mandriva.com> 1.4.6-1
+ Revision: 773959
- 1.4.6 (final)

* Mon Feb 13 2012 Oden Eriksson <oeriksson@mandriva.com> 1.4.6-0.1
+ Revision: 773765
- 1.4.6 (pre-release)

* Wed Feb 08 2012 Oden Eriksson <oeriksson@mandriva.com> 1.4.5-4
+ Revision: 771807
- fix linkage

* Wed Feb 01 2012 Oden Eriksson <oeriksson@mandriva.com> 1.4.5-3
+ Revision: 770375
- make it backportable

* Tue Nov 29 2011 Oden Eriksson <oeriksson@mandriva.com> 1.4.5-2
+ Revision: 735445
- heh...
- fix #64867 (RTLD_DEEPBIND for apr's shared object loading is incompatible with the new mod_dav_svn.so)
- drop the static lib and the libtool *.la file
- various cleanups

* Sat May 21 2011 Oden Eriksson <oeriksson@mandriva.com> 1.4.5-1
+ Revision: 676497
- 1.4.5 (fixes CVE-2011-1928)

* Fri May 20 2011 Oden Eriksson <oeriksson@mandriva.com> 1.4.5-0
+ Revision: 676364
- 1.4.5 (pre-release)

* Mon May 09 2011 Oden Eriksson <oeriksson@mandriva.com> 1.4.4-2
+ Revision: 673022
- fix slight borkiness

* Mon May 09 2011 Oden Eriksson <oeriksson@mandriva.com> 1.4.4-1
+ Revision: 672985
- 1.4.4
- the alias patch (pcpa) was added upstream
- drop redundant aclocaldir patch

* Mon May 02 2011 Oden Eriksson <oeriksson@mandriva.com> 1.4.2-5
+ Revision: 662786
- mass rebuild

* Sun Jan 02 2011 Funda Wang <fwang@mandriva.org> 1.4.2-4mdv2011.0
+ Revision: 627499
- fix build with latest libtool

  + Oden Eriksson <oeriksson@mandriva.com>
    - try to fix the build
    - don't force the usage of automake1.7

* Wed Dec 01 2010 Paulo Andrade <pcpa@mandriva.com.br> 1.4.2-3mdv2011.0
+ Revision: 604557
- Add workaround to code breaking gcc type based alias analysis

* Thu Nov 25 2010 Oden Eriksson <oeriksson@mandriva.com> 1.4.2-2mdv2011.0
+ Revision: 601020
- rebuild

* Sun Jan 31 2010 Oden Eriksson <oeriksson@mandriva.com> 1.4.2-1mdv2010.1
+ Revision: 498781
- 1.4.2

* Wed Dec 30 2009 Oden Eriksson <oeriksson@mandriva.com> 1.3.9-2mdv2010.1
+ Revision: 484228
- rebuild

* Thu Sep 24 2009 Oden Eriksson <oeriksson@mandriva.com> 1.3.9-1mdv2010.0
+ Revision: 448163
- 1.3.9

* Thu Aug 06 2009 Oden Eriksson <oeriksson@mandriva.com> 1.3.8-1mdv2010.0
+ Revision: 410949
- 1.3.8

* Wed Aug 05 2009 Oden Eriksson <oeriksson@mandriva.com> 1.3.8-0.1mdv2010.0
+ Revision: 409996
- 1.3.8

* Tue Aug 04 2009 Götz Waschk <waschk@mandriva.org> 1.3.7-3mdv2010.0
+ Revision: 409404
- fix build deps to catch libuuid dep

* Tue Aug 04 2009 Eugeni Dodonov <eugeni@mandriva.com> 1.3.7-2mdv2010.0
+ Revision: 408927
- rebuild with new libuuid

* Thu Jul 23 2009 Oden Eriksson <oeriksson@mandriva.com> 1.3.7-1mdv2010.0
+ Revision: 398971
- 1.3.7

* Fri Jul 17 2009 Oden Eriksson <oeriksson@mandriva.com> 1.3.6-2mdv2010.0
+ Revision: 396722
- P5: fixes http://www.mail-archive.com/dev@apr.apache.org/msg21843.html

* Tue Jul 07 2009 Oden Eriksson <oeriksson@mandriva.com> 1.3.6-1mdv2010.0
+ Revision: 393171
- 1.3.6 (final)
- disable the tests for now (unknown problem)
- 1.3.6 (pre-release)

* Fri Jun 05 2009 Oden Eriksson <oeriksson@mandriva.com> 1.3.5-1mdv2010.0
+ Revision: 383063
- 1.3.5 (final)

* Thu Jun 04 2009 Oden Eriksson <oeriksson@mandriva.com> 1.3.5-0.1mdv2010.0
+ Revision: 382672
- 1.3.5 (release candidate)
- nuke upstream patches

* Sun Feb 08 2009 Oden Eriksson <oeriksson@mandriva.com> 1.3.3-5mdv2009.1
+ Revision: 338470
- added a couple of upstream fixes

* Sun Feb 08 2009 Oden Eriksson <oeriksson@mandriva.com> 1.3.3-4mdv2009.1
+ Revision: 338465
- fix build with libtool22 (fedora)
- reworked the deepbind patch, RTLD_DEEPBIND is in glibc > 2.3.4
- reorder patches

* Tue Dec 16 2008 Oden Eriksson <oeriksson@mandriva.com> 1.3.3-3mdv2009.1
+ Revision: 314982
- enforce system libtool

* Tue Sep 02 2008 Oden Eriksson <oeriksson@mandriva.com> 1.3.3-2mdv2009.0
+ Revision: 278889
- rebuild

* Sun Aug 17 2008 Oden Eriksson <oeriksson@mandriva.com> 1.3.3-1mdv2009.0
+ Revision: 272946
- 1.3.3 (final)

* Sat Aug 09 2008 Oden Eriksson <oeriksson@mandriva.com> 1.3.3-0.1mdv2009.0
+ Revision: 270068
- 1.3.3 (dev rel)

* Mon Jun 23 2008 Oden Eriksson <oeriksson@mandriva.com> 1.3.2-2mdv2009.0
+ Revision: 227985
- rebuilt due to PayloadIsLzma problems

* Sat Jun 21 2008 Oden Eriksson <oeriksson@mandriva.com> 1.3.2-1mdv2009.0
+ Revision: 227722
- 1.3.2 (release)

* Tue Jun 17 2008 Oden Eriksson <oeriksson@mandriva.com> 1.3.2-0.1mdv2009.0
+ Revision: 223196
- 1.3.2 (unreleased)
- drop the shm_destroy_twice_fix patch, seems not needed anymore

  + Pixel <pixel@mandriva.com>
    - do not call ldconfig in %%post/%%postun, it is now handled by filetriggers

* Sat Jun 07 2008 Oden Eriksson <oeriksson@mandriva.com> 1.3.0-1mdv2009.0
+ Revision: 216698
- bump release

* Wed Jun 04 2008 Oden Eriksson <oeriksson@mandriva.com> 1.3.0-0.1mdv2009.0
+ Revision: 214958
- 1.3.0
- drop upstream implemented patches; P4,P10
- rediffed P1
- added new P10 to fix borked shm tests

* Sat May 24 2008 Oden Eriksson <oeriksson@mandriva.com> 1.2.12-5mdv2009.0
+ Revision: 210860
- apply the deepbind patch as it probably works with our glibc now

* Sat May 17 2008 Oden Eriksson <oeriksson@mandriva.com> 1.2.12-4mdv2009.0
+ Revision: 208455
- rebuild
- fix deps

  + Olivier Blin <blino@mandriva.org>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Thu Dec 13 2007 Oden Eriksson <oeriksson@mandriva.com> 1.2.12-3mdv2008.1
+ Revision: 119425
- put the extra headers in the correct place

* Wed Dec 12 2007 Oden Eriksson <oeriksson@mandriva.com> 1.2.12-2mdv2008.1
+ Revision: 117754
- added more headers
- added P10 from fc9

* Wed Nov 28 2007 Oden Eriksson <oeriksson@mandriva.com> 1.2.12-1mdv2008.1
+ Revision: 113557
- 1.2.12
- drop upstream P10
- run all tests

* Thu Sep 06 2007 Oden Eriksson <oeriksson@mandriva.com> 1.2.11-1mdv2008.0
+ Revision: 80715
- 1.2.11 (release)

* Wed Sep 05 2007 Oden Eriksson <oeriksson@mandriva.com> 1.2.11-0.1mdv2008.0
+ Revision: 79878
- 1.2.11

* Sat Aug 18 2007 Oden Eriksson <oeriksson@mandriva.com> 1.2.9-2mdv2008.0
+ Revision: 65564
- use the new devel package naming
- fix BuildPrereq rpmlint errors

* Sat Jun 23 2007 Oden Eriksson <oeriksson@mandriva.com> 1.2.9-1mdv2008.0
+ Revision: 43422
- 1.2.9
- drop upstream implemented patches; P5

* Sat Jun 23 2007 Oden Eriksson <oeriksson@mandriva.com> 1.2.8-3mdv2008.0
+ Revision: 43403
- use the new %%serverbuild macro

* Thu Jun 07 2007 Oden Eriksson <oeriksson@mandriva.com> 1.2.8-2mdv2008.0
+ Revision: 36655
- use distro conditional -fstack-protector


* Sun Dec 10 2006 Oden Eriksson <oeriksson@mandriva.com> 1.2.8-1mdv2007.0
+ Revision: 94525
- 1.2.8
- drop upstream patches; P0

* Thu Nov 16 2006 Oden Eriksson <oeriksson@mandriva.com> 1.2.7-3mdv2007.1
+ Revision: 84738
- sync with fedora (1.2.7-10)
- Import apr

* Wed Jul 12 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.7-2mdk
- rebuild

* Sat Apr 15 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.7-1mdk
- 1.2.7

* Thu Mar 30 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.6-1mdk
- 1.2.6

* Tue Mar 21 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.5-1mdk
- 1.2.5
- drop upstream patches; P7,P8,P10,P11

* Mon Feb 06 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.2-8mdk
- disable the RTLD_DEEPBIND patch that doesn't seem to work with 
  our glibc and was causing a 5s delay for ssl access (#21012) (P6)

* Mon Feb 06 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.2-7mdk
- fix deps (e2fsprogs-devel for uuid support)

* Sun Feb 05 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.2-6mdk
- drop the ap_compat.h header hack, it messes up a apache head build

* Sat Jan 07 2006 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.2-5mdk
- sync with fedora (1.2.2-7)

* Mon Dec 26 2005 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.2-4mdk
- sync with fedora (1.2.2-4)

* Wed Dec 21 2005 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.2-3mdk
- enable RTLD_DEEPBIND only if supported by glibc (thanks 
  Gwenole Beauchesne)

* Wed Dec 14 2005 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.2-2mdk
- fix deps (spturtle)
- added apr_compat.h with a twist

* Mon Dec 12 2005 Oden Eriksson <oeriksson@mandriva.com> 1:1.2.2-1mdk
- 1.2.2
- merge with the apr package from contrib
- merge fedora changes (1.2.2-2)

* Sun Oct 30 2005 Oden Eriksson <oeriksson@mandriva.com> 1:0.9.7-3mdk
- added P12,P13 from fedora (0.9.6-6)

* Mon Oct 17 2005 Oden Eriksson <oeriksson@mandriva.com> 0.9.7-2mdk
- rebuild

* Tue Oct 11 2005 Oden Eriksson <oeriksson@mandriva.com> 1:0.9.7-1mdk
- 0.9.7
- drop upstream patches; P10,P12,P13

* Mon May 23 2005 Oden Eriksson <oeriksson@mandriva.com> 1:0.9.6-5mdk
- sync with fedora (0.9.6-5)

* Mon May 23 2005 Oden Eriksson <oeriksson@mandriva.com> 1:0.9.6-4mdk
- sync with fedora
- fix requires-on-release

* Fri Mar 18 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.6-3mdk
- use the %%mkrel macro
- drop the metux patch (P30)

* Mon Feb 07 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.6-2mdk
- oops, only half of the P19 patch was implemented

* Mon Feb 07 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.6-1mdk
- 0.9.6
- drop P3 and P19, these are implemented upstream

* Thu Jan 20 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-17mdk
- run the tests in %%install

* Tue Jan 11 2005 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-16mdk
- make --with debug work

* Wed Dec 29 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-15mdk
- revert latest "lib64 fixes"

* Wed Dec 29 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-14mdk
- lib64 fixes

* Thu Nov 25 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-13mdk
- 0.9.5

* Thu Sep 16 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-12mdk
- new P0
- rediffed P2
- new P17, another approach

* Wed Aug 11 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-11mdk
- rebuilt

* Wed Aug 04 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-10mdk
- sync with fedora (0.9.4-17)

* Thu Jul 01 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-9mdk
- new P0
- remove one hunk from P1, partially implemented upstream
- drop P6,P9,P10,P11,P12,P13,P14,P15,P16 and P18,
  the fix is implemented upstream
- drop P8, similar fix is implemented upstream

* Sat Jun 19 2004 Jean-Michel Dault <jmdault@mandrakesoft.com> 0.9.5-8mdk
- rebuild with new openssl

* Fri Jun 18 2004 Jean-Michel Dault <jmdault@mandrakesoft.com> 0.9.5-7mdk
- use fcntl for mutexes instead of posix mutexes (which won't work on
  non-NPTL kernels and some older processors), or sysvsem which are not
  resistand under high load.

* Thu Jun 17 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-6mdk
- sync with fedora

* Fri Jun 11 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-5mdk
- sync with fedora

* Wed May 19 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-4mdk
- sync with fedora

* Wed May 19 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-3mdk
- add the metux mpm hooks (P30)

* Mon May 10 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-2mdk
- oops!, forgot to pass "--cache-file=config.cache" to configure

* Sat May 08 2004 Oden Eriksson <oeriksson@mandrakesoft.com> 0.9.5-1mdk
- initial fedora import and mandrake adaptions

* Wed Mar 24 2004 Joe Orton <jorton@redhat.com> 0.9.4-11
- add APR_LARGEFILE flag

* Mon Mar 15 2004 Joe Orton <jorton@redhat.com> 0.9.4-10
- fix configure check for mmap of /dev/zero
- just put -D_GNU_SOURCE in CPPFLAGS not _{BSD,SVID,XOPEN}_SOURCE

* Tue Mar 02 2004 Elliot Lee <sopwith@redhat.com> 0.9.4-9.1
- rebuilt

* Thu Feb 19 2004 Joe Orton <jorton@redhat.com> 0.9.4-9
- undocument apr_dir_read() ordering constraint and fix tests

* Sun Feb 15 2004 Joe Orton <jorton@redhat.com> 0.9.4-8
- rebuilt without -Wall -Werror

* Fri Feb 13 2004 Elliot Lee <sopwith@redhat.com> 0.9.4-7
- rebuilt

* Tue Feb 03 2004 Joe Orton <jorton@redhat.com> 0.9.4-6
- define apr_off_t as int/long/... to prevent it changing
  with _FILE_OFFSET_BITS on 32-bit platforms

* Mon Jan 12 2004 Joe Orton <jorton@redhat.com> 0.9.4-5
- add apr_temp_dir_get fixes from HEAD

* Thu Jan 08 2004 Joe Orton <jorton@redhat.com> 0.9.4-4
- ensure that libapr is linked against libpthread
- don't link libapr against -lnsl

