c     This program was written to calculate the section of a particle
c     distribution so as to make bar-charts with gnuplot ... it seems
c     gnuplot does not do this ... strange but i could not find it
c     anyway :) please send any comments 2 me (bdm) thank u.
c     seen as they all seem to disagree slightly, i thought i would
c     add 2 the confusion :) send comments 2 me (bdm) thank u :)

      program sec

      integer   npart, res, col
      parameter (npart = %subme2000)
      parameter (res = npart/10) ! (= %subme200 in this case)
      parameter (col = 10) ! number of columns of file 2 b read in
      real*8    uplim(col), dnlim(col)
      real*8    vec(col,npart), step(col), count(col,res), em, me
      integer   tic(col,res), tot1, tot2, tot3, tot4, tot5, tot6
      integer   tot7

      data      uplim/10*0.0/, dnlim/10*0.0/, vec/%subme20000*0.0/
      data      me/1*0.0/, step/10*0.0/, tic/%subme2000*0/
      data      count/%subme2000*0.0/, em/1*0.0/
      data      gam/1*0.0/, bet/1*0.0/
      data      tot1/1*0/, tot2/1*0/, tot3/1*0/
      data      tot4/1*0/, tot5/1*0/, tot6/1*0/
      data      tot7/1*0/

      em = 0.51099906e6
      me = 1.0/em

c     a good resolution to have for a bar chart is 1/100th the number
c     of particles, but this may be changed at will (change res above).
c     below it is assumed that the file to be read from is called
c     'fort.9' - this can also be changed :)

      do 11 i = 1, npart
      read(9,*) vec(1,i), vec(2,i), vec(3,i), vec(4,i), vec(5,i),
     &vec(6,i), vec(7,i), vec(8,i), vec(9,i), vec(10,i)
 11   continue

c     this is to get rid of the astra reference particle difference
c     very important note !!! this not only gets rid of the reference
c     particle but it also sets the entire distribution at z=0 & pz=0
c     this is *very* important as you may not want this ... :)

      vec(3,1) = 0.0
      vec(6,1) = 0.0

      do 22 i = 2, npart
      vec(3,i) = vec(3,i) + vec(3,1)
      vec(6,i) = vec(6,i) + vec(6,1)
 22   continue

      do 23 i = 2, npart
      if ((vec(10,i).le.(0))) then
      vec(3,i) = vec(3,i-1)
      vec(6,i) = vec(6,i-1)
      endif
 23   continue

c     this re-outputs the distribution without reference particle

      do 33 i = 1, npart
      write(8,666) vec(1,i), vec(2,i), vec(3,i), vec(4,i), vec(5,i),
     &vec(6,i), vec(7,i), vec(8,i), vec(9,i), vec(10,i)
 33   continue

      gam = vec(6,1) + 1.0
      bet = sqrt(1 - gam**(-2.0))

      do 44 i = 1, npart
      vec(1,i) = vec(1,i)*1000.0
      vec(2,i) = vec(2,i)*1000.0
      vec(3,i) = vec(3,i)*1000.0
      vec(4,i) = vec(4,i)/1000.0 ! *me
      vec(5,i) = vec(5,i)/1000.0 ! *me
      vec(6,i) = vec(6,i)/1000.0 ! *me
 44   continue

c     this re-outputs the distribution in scaled units

      do i = 1, npart
      write(99,666) vec(1,i), vec(2,i), vec(3,i), vec(4,i), vec(5,i),
     &vec(6,i), vec(7,i), vec(8,i), vec(9,i), vec(10,i)
      enddo
      
      do 10 k = 1, col
      uplim(k) = vec(k,1)
      dnlim(k) = vec(k,1)
 10   continue

      do 20 k = 1, col
      do 55 i = 1, npart
      if ((vec(k,i)).ge.(uplim(k))) then
      uplim(k) = vec(k,i)
      endif
      if ((vec(k,i)).le.(dnlim(k))) then
      dnlim(k) = vec(k,i)
      endif
 55   continue
 20   continue

      write(*,555) uplim
      write(*,555) dnlim

      write(7,555) (uplim + dnlim)/2.0

      do 30 k = 1, col
      step(k) = (uplim(k) - dnlim(k))/res
 30   continue

      do 3 j = 1, res
      do 2 i = 1, npart
      do 1 k = 1, col

      count(k,j)  = dnlim(k) + (j - 1/2)*step(k)

      if ((vec(k,i)).ge.(dnlim(k) + (j - 1)*step(k))) then
      if ((vec(k,i)).le.(dnlim(k) + j*step(k))) then
      tic(k,j) = tic(k,j) + 1
      endif
      endif

 1    continue
 2    continue
 3    continue

      do 1001 j = 1, res

c      count(6,j) = count(6,j)*em/1000000.0

      write(11,777) count(1,j), tic(1,j), count(2,j), tic(2,j),
     &count(3,j), tic(3,j), count(4,j), tic(4,j), count(5,j),
     &tic(5,j), count(6,j), tic(6,j), count(7,j), tic(7,j)

 1001 continue

c     below is just a check, all totals should be more or less (+/- 1) the
c     same as the number of particles.

      do j = 1, res
      tot1 = tot1 + tic(1,j)
      tot2 = tot2 + tic(2,j)
      tot3 = tot3 + tic(3,j)
      tot4 = tot4 + tic(4,j)
      tot5 = tot5 + tic(5,j)
      tot6 = tot6 + tic(6,j)
      tot7 = tot7 + tic(7,j)
      enddo

      write(*,*) tot1, tot2, tot3, tot4, tot5, tot6, tot7

 555  format(10f10.2)

 666  format(e13.5,1x,e13.5,1x,e13.5,1x,e13.5,1x,e13.5,1x,e13.5,
     &1x,e13.5,1x,e10.2,1x,f5.1,1x,f5.1)

 777  format(10(e13.5,1x,i4))

      end
