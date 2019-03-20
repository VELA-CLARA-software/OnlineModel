c     program to calculate the tails of distributions
c     this is incredibly inelegant - i know - but it is the *only* way
c     i know how to do this ... :) i am sure there are better ways but
c     i do not know them yet ... :)
c     written by bdm 22/09/15, comments welcome :)
c     last updated by bdm 22/09/15


      program tails

      integer   tot

      parameter(tot = %subme2 - %subme1)

      integer   boto, topo

      boto = %subme1
      topo = %subme2

      if(boto.eq.topo) then
      write(*,*) 'nothing to compare you fool !!!'
      endif

      do i = 0, tot
      write(66,666) boto + i, boto, topo
      enddo

 666  format('./tails ', i3, ' ', i3, ' ', i3)

      end
