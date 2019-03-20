c     this program attempts to calculate the inverse of a simple
c     six by six transfer matrix used in accelerator physics. this
c     program also tries to sort out the slight mix-up which may
c     have happened between values i,j and j,i of an arbitrary
c     matrix (i.e. using mat(i,j) instead of mat(j,i) or v.v.)

      program rotate

      integer   npart, res, col
      parameter (npart = %subme2000)
      parameter (col = 8) ! number of columns of file 2 b read in
      real*8    vec(col,npart), rvec(col,npart), theta, pi
      real*8    nvec(col,npart), rmat(6,6), zoff
      integer   veci(2,npart)

c      data      vec/4096*0.0/, rvec/4096*0.0/, nvec/4096*0.0/
c      data      theta/1*0.0/, pi/1*0.0/, zoff/0.0/
c      data      rmat/36*0.0/, veci/1024*0/

      pi = dacos(- 1.0d + 0)

      call readv(vec,veci,9,col,npart)

c      theta = -45*pi/180.0 ! theta is -45 degrees to test here but ... :)
      theta = %subtheta*pi/180.0

c     the line below is crucial to recentering the bunch as it goes through
c     the dipole & it includes the offset of where exactly the dipole starts ...

      zoff = %subzoff

      vec(3,1) = zoff*cos(theta)

      call norm(nvec,vec,col,npart) ! this removes the rp from vec & gives nvec

      call check(nvec,veci,col,npart) ! checks for lost particles & replaces them

      call writev(vec,veci,10,col,npart) ! this is the dist. *with* the rp

      call writev(nvec,veci,11,col,npart) ! this is the dist. *without* rp

      call rot(rmat,theta) ! calls the rotation matrix

      call zero(vec,col,npart) ! sets first 6 cols of vec to zero

      call unnorm(vec,nvec,col,npart) ! this re-introduces the rp to nvec & gives vec

      call writev(vec,veci,12,col,npart) ! this is the dist *with* the rp

      call writev(nvec,veci,13,col,npart) ! this is the dist. *without* rp

      call mult(rvec,rmat,nvec,col,npart) ! this rotates nvec to rvec

      call zero(vec,col,npart) ! sets first 6 cols of vec to zero

      call unnorm(vec,rvec,col,npart) ! this re-introduces the rp to rvec & gives vec

      call writev(rvec,veci,14,col,npart) ! the rotated bunch *without* rp

      write(*,*) vec(1,1), vec(3,1), zoff

      vec(3,1) = zoff

      write(*,*) vec(3,1), zoff

      call writev(vec,veci,15,col,npart) ! the rotated bunch *with* the rp

      call write(rmat) ! writes the rotation matrix to check ... :)

      end

      subroutine check(v,vi,col,npart)

      integer   npart, col, vi(2,npart), jj
      real*8    v(col,npart), avr(col)

      do 1 i = 1, npart
          if (vi(2,i).le.0) then
              jj = i
              call av(v,avr,col,npart,jj)
                  do 11 j = 1, col
                      v(j,i) = avr(j)
                      write(88,*) v(j,i)
 11               continue
              vi(1,i) = 1
              vi(2,i) = 5
              write(3,*) ' '
              write(3,333) i
              write(3,*) ' '
              write(3,444)
          endif
 1    continue

 333  format('particle',i5,' lost & replaced with particle averages')
 444  format('please investigate ... :)')

      return

      end

      subroutine av(v,avr,col,npart,jj)

      integer   npart, col, jj, np
      real*8    v(col,npart), avr(col)

      np = npart

      do 11 j = 1, col
          do 101 i = 1, npart
              if (i.eq.jj) then
                  if (j.eq.1) then
                      np = np - 1
                  endif
              else
                  avr(j) = avr(j) + v(j,i)
              endif
 101      continue
          avr(j) = avr(j)/np
      write(4,*) avr(j), np
 11   continue

      return 

      end

      subroutine norm(nv,v,col,npart)

      integer   npart, col
      real*8    nv(col,npart), v(col,npart)

      do 1 i = 1, npart
          nv(1,i) = v(1,i)
          nv(2,i) = v(2,i)
          nv(4,i) = v(4,i)
          nv(5,i) = v(5,i)
          nv(7,i) = v(7,i)
          nv(8,i) = v(8,i)
 1    continue

      nv(3,1) = v(3,1)
      nv(6,1) = v(6,1)

      do 2 i = 2, npart
          nv(3,i) = 0.0
          nv(6,i) = 0.0
 2    continue

      do 3 i = 2, npart
          nv(3,i) = v(3,i) + v(3,1)
          nv(6,i) = v(6,i) + v(6,1)
 3    continue

      return

      end

      subroutine unnorm(nv,v,col,npart)

      integer   npart, col
      real*8    nv(col,npart), v(col,npart)

      do 1 i = 1, npart
          nv(1,i) = v(1,i)
          nv(2,i) = v(2,i)
          nv(4,i) = v(4,i)
          nv(5,i) = v(5,i)
          nv(7,i) = v(7,i)
          nv(8,i) = v(8,i)
 1    continue

      nv(3,1) = v(3,1)
      nv(6,1) = v(6,1)

      do 2 i = 2, npart
          nv(3,i) = 0.0
          nv(6,i) = 0.0
 2    continue

      do 3 i = 2, npart
          nv(3,i) = v(3,i) - v(3,1)
          nv(6,i) = v(6,i) - v(6,1)
 3    continue

      return

      end

      subroutine romesq(v,rms,col,npart)

      integer   col, npart, tot
      real*8    v(col,npart), vsq(col,npart), av(col), rms(col)

      tot = 1.0*npart

      do 11 i = 1, col
          do 101 j = 1, npart
              vsq(i,j) = v(i,j)**2
 101      continue
 11   continue

      do 22 i = 1, col
          do 202 j = 1, npart
              av(i) = av(i) + vsq(i,j)
 202      continue
 22   continue

      do 33 i = 1, col
          av(i) = av(i)/tot
 33   continue

      do 44 i = 1, col
          rms(i) = sqrt(av(i))
 44   continue

      write(*,*) rms

      return

      end

      subroutine rot(xmat,theta)

      real*8    xmat(6,6), theta

      xmat(1,1) = cos(theta)
      xmat(1,3) = - sin(theta)
      xmat(2,2) = 1.0
      xmat(3,1) = sin(theta)
      xmat(3,3) = cos(theta)
c      xmat(4,4) = 1.0
c      xmat(5,5) = 1.0
c      xmat(6,6) = 1.0
      xmat(4,4) = cos(theta)
      xmat(4,6) = - sin(theta)
      xmat(5,5) = 1.0
      xmat(6,4) = sin(theta)
      xmat(6,6) = cos(theta)

      return

      end

      subroutine equiv(xmat,ymat)

      real*8    xmat(6,6), ymat(6,6)

      do 2 i = 1, 6
          do 1 j = 1, 6
              xmat(i,j) = ymat(i,j)
 1        continue
 2    continue

      return

      end

      subroutine zero(v,col,npart)

      integer   npart, col
      real*8    v(col,npart)

      do 1 i = 1, 6
          do 2 j = 1, npart
              v(i,j) = 0.0
 2        continue
 1    continue

      return

      end

      subroutine mean(v,avr,col,npart)

      integer   npart, col
      real*8    v(col,npart), avr(col)

      do 11 j = 1, col
          do 101 i = 1, npart
              avr(j) = avr(j) + v(j,i)
 101      continue
          avr(j) = avr(j)/npart
 11   continue

      write(4,*) avr

      return 

      end

      subroutine mult(rv,rmat,v,col,npart)

      integer   npart, col
      real*8    rv(col,npart), rmat(6,6), v(col,npart)

c     make sure that the vector we start with is zero throughout :)
c     this may not be necessary but ... :) in fact this is *not* at
c     all necessary but i do believe it is good practice (i seem to
c     remember werner telling me this but ...)

      call zero(rv,col,npart)

c     now we do rv = rmat*v

      do 3 i = 1, npart
          do 2 j = 1, 6
              do 1 k = 1, 6
                  rv(j,i) = rv(j,i) + rmat(j,k)*v(k,i)
 1            continue
 2        continue
 3    continue

c     note: we missed out an important part & this meant that the
c     last two columns came out as zeros ... :| we could redefine
c     the multiplication matrix to be 8x8 but this is complicated
c     & we will do so later - if at all ...

      do 4 i = 1, npart
          rv(7,i) = v(7,i)
          rv(8,i) = v(8,i)
 4    continue
      
      return

      end

      subroutine write(xmat)

c     this subroutine just writes the raw data of anything in row and
c     block format for plotting purposes or anything else

      real*8    xmat(6,6)

      write(7,6661) xmat(1,1),xmat(1,2),xmat(1,3),xmat(1,4),xmat(1,5),
     &xmat(1,6),xmat(2,1),xmat(2,2),xmat(2,3),xmat(2,4),xmat(2,5),
     &xmat(2,6),xmat(3,1),xmat(3,2),xmat(3,3),xmat(3,4),xmat(3,5),
     &xmat(3,6),xmat(4,1),xmat(4,2),xmat(4,3),xmat(4,4),xmat(4,5),
     &xmat(4,6),xmat(5,1),xmat(5,2),xmat(5,3),xmat(5,4),xmat(5,5),
     &xmat(5,6),xmat(6,1),xmat(6,2),xmat(6,3),xmat(6,4),xmat(6,5),
     &xmat(6,6)

 6661 format(36f13.9)

 7771 format(6f16.12) ! this should be equivalent to astra high_res = t

 8881 format(6e12.4) ! this is what astra uses at low res ...

 9991 format(6e20.12) ! this is what astra uses when high_res = t ... :)

      return

      end

      subroutine writev(v,vi,num,col,npart)

      integer   npart, col, num, vi(2,npart)
      real*8    v(col,npart)

      do 1 i = 1, npart
      write(num,999) v(1,i), v(2,i), v(3,i), v(4,i), v(5,i),
     &v(6,i), v(7,i), v(8,i), vi(1,i), vi(2,i)
 1    continue

 666  format(1p,e13.5,1x,e13.5,1x,e13.5,1x,e13.5,1x,e13.5,1x,e13.5,
     &1x,e13.5,1x,e10.2,1x,i4,1x,i4)

 777  format(8f16.12,2i4) ! this should be equivalent to astra high_res = t

 888  format(8e12.4,2i4) ! this is what astra uses at low res ...

 999  format(1p,8e20.12,2i4) ! this is what astra uses when high_res = t ... :)

      return

      end

      subroutine readv(v,vi,num,col,npart)

      integer   npart, col, num, vi(2,npart)
      real*8    v(col,npart)

      do 1 i = 1, npart
      read(num,999) v(1,i), v(2,i), v(3,i), v(4,i), v(5,i),
     &v(6,i), v(7,i), v(8,i), vi(1,i), vi(2,i)
 1    continue

 666  format(1p,e13.5,1x,e13.5,1x,e13.5,1x,e13.5,1x,e13.5,1x,e13.5,
     &1x,e13.5,1x,e10.2,1x,i4,1x,i4)

 777  format(8f16.12,2i4) ! this should be equivalent to astra high_res = t

 888  format(8e12.4,2i4) ! this is what astra uses at low res ...

 999  format(1p,8e20.12,2i4) ! this is what astra uses when high_res = t ... :)

      return

      end

c do i=1,msize
c    rsumaux=rzero
c    rsum=rzero
c    do k=1,msize
c       rsumaux=A(i,k)*x(k)
c       rsum=rsum+rsumaux
c       enddo
c       b(i)=rsum
c enddo
