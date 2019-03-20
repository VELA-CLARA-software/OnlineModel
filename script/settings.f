c     this program was written to calculate the settings of the relevant
c     astra runs to be compared (in particular the second astra run seen
c     as only two runs are compared at any one time). please send comments
c     to me (bdm) 21/08/06, i know full well that it can be done in much
c     better and especially more elegant ways so you can save yourself
c     time and don't have to make that comment ... :) the way this works
c     is by writing a script from this fortran program ... another script
c     then executes it ... like i said ... not at all elegant but it does
c     the job ... if you know any better way of doing this please let me 
c     (bdm) know ... in am sure there is one ... :)
c     last updated 26/11/18

      program sets

      integer run1, run2, mp1, mp2, sc1, sc2, msc1, msc2
      integer end11, end12, end21, end22
      real*8  ch1, ch2, ss1, ss2, l1g1, l1g2, gg1, gg2, gp1, gp2
      real*8  pl1, pl2, l1p1, l1p2, bcs1, bcs2, l1s11, l1s12
      real*8  l1s21, l1s22, s02q11, s02q12, s02q21, s02q22
      real*8  s02q31, s02q32, s02q41, s02q42, c2vq11, c2vq12
      real*8  c2vq21, c2vq22, c2vq31, c2vq32, vq11, vq12, vq21, vq22
      real*8  vq31, vq32, vq41, vq42, vq51, vq52, vq61, vq62
      real*8  ba1q11, ba1q12, ba1q21, ba1q22, ba1q31, ba1q32
      real*8  ba1q41, ba1q42, ba1q51, ba1q52, ba1q61, ba1q62
      real*8  ba1q71, ba1q72

      data    run1/1*0/, run2/1*0/, mp1/1*0/, mp2/1*0/, end11/1*0/
      data    end12/1*0/, sc1/1*0/, sc2/1*0/, ch1/1*0.0/, ch2/1*0.0/
      data    ss1/1*0.0/, ss2/1*0.0/, l1g1/1*0.0/, l1g2/1*0.0/
      data    gg1/1*0.0/, gg2/1*0.0/, gp1/1*0.0/, gp2/1*0.0/
      data    l1p1/1*0.0/, l1p2/1*0.0/, bcs1/1*0.0/, bcs2/1*0.0/
      data    l1s11/1*0.0/, l1s12/1*0.0/, l1s21/1*0.0/, l1s22/1*0.0/
      data    s02q11/1*0.0/, s02q12/1*0.0/, s02q21/1*0.0/, s02q22/1*0.0/
      data    s02q31/1*0.0/, s02q32/1*0.0/, s02q41/1*0.0/, s02q42/1*0.0/
      data    c2vq11/1*0.0/, c2vq12/1*0.0/, c2vq21/1*0.0/, c2vq22/1*0.0/
      data    c2vq31/1*0.0/, c2vq32/1*0.0/, vq11/1*0.0/, vq12/1*0.0/
      data    vq21/1*0.0/, vq22/1*0.0/, vq31/1*0.0/, vq32/1*0.0/
      data    vq41/1*0.0/, vq42/1*0.0/, vq51/1*0.0/, vq52/1*0.0/
      data    vq61/1*0.0/, vq62/1*0.0/, ba1q11/1*0.0/, ba1q12/1*0.0/
      data    ba1q21/1*0.0/, ba1q22/1*0.0/, ba1q31/1*0.0/, ba1q32/1*0.0/
      data    ba1q41/1*0.0/, ba1q42/1*0.0/, ba1q51/1*0.0/, ba1q52/1*0.0/
      data    ba1q61/1*0.0/, ba1q62/1*0.0/, ba1q71/1*0.0/, ba1q72/1*0.0/
      data    pl1/1*0.0/, pl2/1*0.0/, end21/1*0/, end22/1*0/
      data    msc1/1*0/, msc2/1*0/

c     fort.21 contains the parameters of the first astra run to be used in
c     the script post_pro whereas fort.22 contains the parameters of the
c     second.

      read(21,*) run1, mp1, pl1, ss1, ch1, gg1, gp1, l1g1, l1p1,
     &bcs1, l1s11, l1s21, end11, sc1, s02q11, s02q21, s02q31, s02q41,
     &c2vq11, c2vq21, c2vq31, vq11, vq21, vq31, vq41, vq51, vq61,
     &ba1q11, ba1q21, ba1q31, ba1q41, ba1q51, ba1q61, ba1q71, msc1
      read(22,*) run2, mp2, pl2, ss2, ch2, gg2, gp2, l1g2, l1p2,
     &bcs2, l1s12, l1s22, end12, sc2, s02q12, s02q22, s02q32, s02q42,
     &c2vq12, c2vq22, c2vq32, vq12, vq22, vq32, vq42, vq52, vq62,
     &ba1q12, ba1q22, ba1q32, ba1q42, ba1q52, ba1q62, ba1q72, msc2

      write(24,777) run1, mp1, pl1, ss1, ch1, gg1, gp1, l1g1, l1p1,
     &bcs1, l1s11, l1s21, end11, sc1, s02q11, s02q21, s02q31, s02q41,
     &c2vq11, c2vq21, c2vq31, vq11, vq21, vq31, vq41, vq51, vq61,
     &ba1q11, ba1q21, ba1q31, ba1q41, ba1q51, ba1q61, ba1q71, msc1
      write(24,*) ' '
      write(24,*) run2, mp2, pl2, ss2, ch2, gg2, gp2, l1g2, l1p2,
     &bcs2, l1s12, l1s22, end12, sc2, s02q12, s02q22, s02q32, s02q42,
     &c2vq12, c2vq22, c2vq32, vq12, vq22, vq32, vq42, vq52, vq62,
     &ba1q12, ba1q22, ba1q32, ba1q42, ba1q52, ba1q62, ba1q72, msc2

      if (run1.eq.run2) then
      write(*,*) ' '
      write(*,*) 'it is useless to compare a run with itself ... :)'
      write(*,*) 'but i shall do so anyway ... just for you ... :)'
      endif

c     as the first line ending with end11 & end12 respectively for the
c     for the two different runs being compared is supposed to be dealt
c     with via separate files, it will not be used here and the lines
c     "if (end11.eq.en12) then" & "endif" are missing ... :)

c     we comment the below out as i do not think it will ever be used
c     again but i am not deleting it just yet ... :) the corresponding
c     of the if "loop" at the end is also commented out ...

c      if (end21.eq.end22) then

c     the lines below write the initial lines at the top of any script
c     giving a short explanation of what is what & what it does ... :)

      write(23,1)
      write(23,2)
      write(23,3)
      write(23,4)

 1    format('#!/bin/tcsh')
 2    format('# script to create compare and run it')
 3    format('# run with: ./compare')
 4    format('# written by bdm, comments welcome :)')

      write(23,*) ' '
      write(23,44)
      write(23,55)
      write(23,66)
      write(23,77)
      write(23,88)
      write(23,99)

 44   format('set input1 = $1 # number of first astra run')
 55   format('set input2 = $2 # number of second astra run')
 66   format('#set input3 = $3 # old description now all internal')
 77   format('#set input4 = $4 # old description now all internal')
 88   format('set input3 = $3 # additional description (1st run)')
 99   format('set input4 = $4 # additional description (2nd run)')

      write(23,*) ' '

      write(23,5)

c     comment out either of the two lines below according to what you want :)

c 5    format('cat gpastra_${input1}_mask2.txt | %ret')
c      note: this is not used any more - this line is kept just in case
c      i find a better way of doing things ... :)

 5    format('cat gpastra_${input1}_mask2.txt | %ret')

      write(23,555) run1
      write(23,666) run2

 555  format('sed -e "s/%sub1/',i3,'/g" %ret')
 666  format('    -e "s/%sub2/',i3,'/g" %ret')

      if (mp1.eq.mp2) then
      write(23,100)
      write(23,101)
 100  format('    -e "s/%sbsta2//g" %ret')
 101  format('    -e "s/%sbstb2//g" %ret')
      else
      write(23,200) mp1
      write(23,201) mp2
 200  format('    -e "s/%sbsta2/',i3,'k MP;/g" %ret')
 201  format('    -e "s/%sbstb2/',i3,'k MP;/g" %ret')
      endif

      if (ch1.eq.ch2) then
      write(23,102)
      write(23,103)
 102  format('    -e "s/%sbsta3//g" %ret')
 103  format('    -e "s/%sbstb3//g" %ret')
      else
      write(23,202) ch1
      write(23,203) ch2
 202  format('    -e "s/%sbsta3/',f5.3,' nC;/g" %ret')
 203  format('    -e "s/%sbstb3/',f5.3,' nC;/g" %ret')
      endif

      if (gg1.eq.gg2) then
      write(23,104)
      write(23,105)
 104  format('    -e "s/%sbsta4//g" %ret')
 105  format('    -e "s/%sbstb4//g" %ret')
      else
      write(23,204) gg1
      write(23,205) gg2
 204  format('    -e "s/%sbsta4/Gun = ',f6.2,' MV%ret/m;/g" %ret')
 205  format('    -e "s/%sbstb4/Gun = ',f6.2,' MV%ret/m;/g" %ret')
      endif

      if (gp1.eq.gp2) then
      write(23,106)
      write(23,107)
 106  format('    -e "s/%sbsta5//g" %ret')
 107  format('    -e "s/%sbstb5//g" %ret')
      else
      write(23,206) gp1
      write(23,207) gp2
 206  format('    -e "s/%sbsta5/Gun = ',f5.1,'^o;/g" %ret')
 207  format('    -e "s/%sbstb5/Gun = ',f5.1,'^o;/g" %ret')
      endif

      if (pl1.eq.pl2) then
      write(23,108)
      write(23,109)
 108  format('    -e "s/%sbsta6//g" %ret')
 109  format('    -e "s/%sbstb6//g" %ret')
      else
      write(23,208) pl1
      write(23,209) pl2
 208  format('    -e "s/%sbsta6/Laser = ',f5.2,' ps;/g" %ret')
 209  format('    -e "s/%sbstb6/Laser = ',f5.2,' ps;/g" %ret')
      endif

      if (ss1.eq.ss2) then
      write(23,110)
      write(23,111)
 110  format('    -e "s/%sbsta7//g" %ret')
 111  format('    -e "s/%sbstb7//g" %ret')
      else
      write(23,210) ss1
      write(23,211) ss2
 210  format('    -e "s/%sbsta7/Spot/4 = ',f5.3,' mm;/g" %ret')
 211  format('    -e "s/%sbstb7/Spot/4 = ',f5.3,' mm;/g" %ret')
      endif

      if (l1g1.eq.l1g2) then
      write(23,112)
      write(23,113)
 112  format('    -e "s/%sbsta8//g" %ret')
 113  format('    -e "s/%sbstb8//g" %ret')
      else
      write(23,212) l1g1
      write(23,213) l1g2
 212  format('    -e "s/%sbsta8/Linac1 = ',f6.2,' MV%ret/m;/g" %ret')
 213  format('    -e "s/%sbstb8/Linac1 = ',f6.2,' MV%ret/m;/g" %ret')
      endif

      if (l1p1.eq.l1p2) then
      write(23,114)
      write(23,115)
 114  format('    -e "s/%sbsta9//g" %ret')
 115  format('    -e "s/%sbstb9//g" %ret')
      else
      write(23,214) l1p1
      write(23,215) l1p2
 214  format('    -e "s/%sbsta9/Linac1 = ',f5.1,'^o;/g" %ret')
 215  format('    -e "s/%sbstb9/Linac1 = ',f5.1,'^o;/g" %ret')
      endif

      if (bcs1.eq.bcs2) then
      write(23,116)
      write(23,117)
 116  format('    -e "s/%sbstaa//g" %ret')
 117  format('    -e "s/%sbstba//g" %ret')
      else
      write(23,216) bcs1
      write(23,217) bcs2
 216  format('    -e "s/%sbstaa/Bucksol = ',f6.3,' T;/g" %ret')
 217  format('    -e "s/%sbstba/Bucksol = ',f6.3,' T;/g" %ret')
      endif

      if (l1s11.eq.l1s12) then
      write(23,118)
      write(23,119)
 118  format('    -e "s/%sbstab//g" %ret')
 119  format('    -e "s/%sbstbb//g" %ret')
      else
      write(23,218) l1s11
      write(23,219) l1s12
 218  format('    -e "s/%sbstab/L1sol1 = ',f6.3,' T;/g" %ret')
 219  format('    -e "s/%sbstbb/L1sol1 = ',f6.3,' T;/g" %ret')
      endif

      if (l1s21.eq.l1s22) then
      write(23,120)
      write(23,121)
 120  format('    -e "s/%sbstac//g" %ret')
 121  format('    -e "s/%sbstbc//g" %ret')
      else
      write(23,220) l1s21
      write(23,221) l1s22
 220  format('    -e "s/%sbstac/L1sol2 = ',f6.3,' T;/g" %ret')
 221  format('    -e "s/%sbstbc/L1sol2 = ',f6.3,' T;/g" %ret')
      endif

c     note: there is *no* "d" label as this is the end of the injector line
c     there is no "e" label either because this appears later & together
c     with what will be the "z" label when i get around to it ... :)

      if (s02q11.eq.s02q12) then
      write(23,122)
      write(23,123)
 122  format('    -e "s/%sbstaf//g" %ret')
 123  format('    -e "s/%sbstbf//g" %ret')
      else
      write(23,222) s02q11
      write(23,223) s02q12
 222  format('    -e "s/%sbstaf/S02Q1 = ',f9.5,' k;/g" %ret')
 223  format('    -e "s/%sbstbf/S02Q1 = ',f9.5,' k;/g" %ret')
      endif

      if (s02q21.eq.s02q22) then
      write(23,124)
      write(23,125)
 124  format('    -e "s/%sbstag//g" %ret')
 125  format('    -e "s/%sbstbg//g" %ret')
      else
      write(23,224) s02q21
      write(23,225) s02q22
 224  format('    -e "s/%sbstag/S02Q2 = ',f9.5,' k;/g" %ret')
 225  format('    -e "s/%sbstbg/S02Q2 = ',f9.5,' k;/g" %ret')
      endif

      if (s02q31.eq.s02q32) then
      write(23,126)
      write(23,127)
 126  format('    -e "s/%sbstah//g" %ret')
 127  format('    -e "s/%sbstbh//g" %ret')
      else
      write(23,226) s02q31
      write(23,227) s02q32
 226  format('    -e "s/%sbstah/S02Q3 = ',f9.5,' k;/g" %ret')
 227  format('    -e "s/%sbstbh/S02Q3 = ',f9.5,' k;/g" %ret')
      endif

      if (s02q41.eq.s02q42) then
      write(23,128)
      write(23,129)
 128  format('    -e "s/%sbstai//g" %ret')
 129  format('    -e "s/%sbstbi//g" %ret')
      else
      write(23,228) s02q41
      write(23,229) s02q42
 228  format('    -e "s/%sbstai/S02Q4 = ',f9.5,' k;/g" %ret')
 229  format('    -e "s/%sbstbi/S02Q4 = ',f9.5,' k;/g" %ret')
      endif

      if (c2vq11.eq.c2vq12) then
      write(23,130)
      write(23,131)
 130  format('    -e "s/%sbstaj//g" %ret')
 131  format('    -e "s/%sbstbj//g" %ret')
      else
      write(23,230) c2vq11
      write(23,231) c2vq12
 230  format('    -e "s/%sbstaj/C2VQ1 = ',f9.5,' k;/g" %ret')
 231  format('    -e "s/%sbstbj/C2VQ1 = ',f9.5,' k;/g" %ret')
      endif

      if (c2vq21.eq.c2vq22) then
      write(23,132)
      write(23,133)
 132  format('    -e "s/%sbstak//g" %ret')
 133  format('    -e "s/%sbstbk//g" %ret')
      else
      write(23,232) c2vq21
      write(23,233) c2vq22
 232  format('    -e "s/%sbstak/C2VQ2 = ',f9.5,' k;/g" %ret')
 233  format('    -e "s/%sbstbk/C2VQ2 = ',f9.5,' k;/g" %ret')
      endif

      if (c2vq31.eq.c2vq32) then
      write(23,134)
      write(23,135)
 134  format('    -e "s/%sbstal//g" %ret')
 135  format('    -e "s/%sbstbl//g" %ret')
      else
      write(23,234) c2vq31
      write(23,235) c2vq32
 234  format('    -e "s/%sbstal/C2VQ3 = ',f9.5,' k;/g" %ret')
 235  format('    -e "s/%sbstbl/C2VQ3 = ',f9.5,' k;/g" %ret')
      endif

      if (vq11.eq.vq12) then
      write(23,136)
      write(23,137)
 136  format('    -e "s/%sbstam//g" %ret')
 137  format('    -e "s/%sbstbm//g" %ret')
      else
      write(23,236) vq11
      write(23,237) vq12
 236  format('    -e "s/%sbstam/VELQ1 = ',f9.5,' k;/g" %ret')
 237  format('    -e "s/%sbstbm/VELQ1 = ',f9.5,' k;/g" %ret')
      endif

      if (vq21.eq.vq22) then
      write(23,138)
      write(23,139)
 138  format('    -e "s/%sbstan//g" %ret')
 139  format('    -e "s/%sbstbn//g" %ret')
      else
      write(23,238) vq21
      write(23,239) vq22
 238  format('    -e "s/%sbstan/VELQ2 = ',f9.5,' k;/g" %ret')
 239  format('    -e "s/%sbstbn/VELQ2 = ',f9.5,' k;/g" %ret')
      endif

      if (vq31.eq.vq32) then
      write(23,140)
      write(23,141)
 140  format('    -e "s/%sbstao//g" %ret')
 141  format('    -e "s/%sbstbo//g" %ret')
      else
      write(23,240) vq31
      write(23,241) vq32
 240  format('    -e "s/%sbstao/VELQ3 = ',f9.5,' k;/g" %ret')
 241  format('    -e "s/%sbstbo/VELQ3 = ',f9.5,' k;/g" %ret')
      endif

      if (vq41.eq.vq42) then
      write(23,142)
      write(23,143)
 142  format('    -e "s/%sbstap//g" %ret')
 143  format('    -e "s/%sbstbp//g" %ret')
      else
      write(23,242) vq41
      write(23,243) vq42
 242  format('    -e "s/%sbstap/VELQ4 = ',f9.5,' k;/g" %ret')
 243  format('    -e "s/%sbstbp/VELQ4 = ',f9.5,' k;/g" %ret')
      endif

      if (vq51.eq.vq52) then
      write(23,144)
      write(23,145)
 144  format('    -e "s/%sbstaq//g" %ret')
 145  format('    -e "s/%sbstbq//g" %ret')
      else
      write(23,244) vq51
      write(23,245) vq52
 244  format('    -e "s/%sbstaq/VELQ5 = ',f9.5,' k;/g" %ret')
 245  format('    -e "s/%sbstbq/VELQ5 = ',f9.5,' k;/g" %ret')
      endif

      if (vq61.eq.vq62) then
      write(23,146)
      write(23,147)
 146  format('    -e "s/%sbstar//g" %ret')
 147  format('    -e "s/%sbstbr//g" %ret')
      else
      write(23,246) vq61
      write(23,247) vq62
 246  format('    -e "s/%sbstar/VELQ6 = ',f9.5,' k;/g" %ret')
 247  format('    -e "s/%sbstbr/VELQ6 = ',f9.5,' k;/g" %ret')
      endif

      if (ba1q11.eq.ba1q12) then
      write(23,148)
      write(23,149)
 148  format('    -e "s/%sbstas//g" %ret')
 149  format('    -e "s/%sbstbs//g" %ret')
      else
      write(23,248) ba1q11
      write(23,249) ba1q12
 248  format('    -e "s/%sbstas/BA1Q1 = ',f9.5,' k;/g" %ret')
 249  format('    -e "s/%sbstbs/BA1Q1 = ',f9.5,' k;/g" %ret')
      endif

      if (ba1q21.eq.ba1q22) then
      write(23,150)
      write(23,151)
 150  format('    -e "s/%sbstat//g" %ret')
 151  format('    -e "s/%sbstbt//g" %ret')
      else
      write(23,250) ba1q21
      write(23,251) ba1q22
 250  format('    -e "s/%sbstat/BA1Q2 = ',f9.5,' k;/g" %ret')
 251  format('    -e "s/%sbstbt/BA1Q2 = ',f9.5,' k;/g" %ret')
      endif

      if (ba1q31.eq.ba1q32) then
      write(23,152)
      write(23,153)
 152  format('    -e "s/%sbstau//g" %ret')
 153  format('    -e "s/%sbstbu//g" %ret')
      else
      write(23,252) ba1q31
      write(23,253) ba1q32
 252  format('    -e "s/%sbstau/BA1Q3 = ',f9.5,' k;/g" %ret')
 253  format('    -e "s/%sbstbu/BA1Q3 = ',f9.5,' k;/g" %ret')
      endif

      if (ba1q41.eq.ba1q42) then
      write(23,154)
      write(23,155)
 154  format('    -e "s/%sbstav//g" %ret')
 155  format('    -e "s/%sbstbv//g" %ret')
      else
      write(23,254) ba1q41
      write(23,255) ba1q42
 254  format('    -e "s/%sbstav/BA1Q4 = ',f9.5,' k;/g" %ret')
 255  format('    -e "s/%sbstbv/BA1Q4 = ',f9.5,' k;/g" %ret')
      endif

      if (ba1q51.eq.ba1q52) then
      write(23,156)
      write(23,157)
 156  format('    -e "s/%sbstaw//g" %ret')
 157  format('    -e "s/%sbstbw//g" %ret')
      else
      write(23,256) ba1q51
      write(23,257) ba1q52
 256  format('    -e "s/%sbstaw/BA1Q5 = ',f9.5,' k;/g" %ret')
 257  format('    -e "s/%sbstbw/BA1Q5 = ',f9.5,' k;/g" %ret')
      endif

      if (ba1q61.eq.ba1q62) then
      write(23,158)
      write(23,159)
 158  format('    -e "s/%sbstax//g" %ret')
 159  format('    -e "s/%sbstbx//g" %ret')
      else
      write(23,258) ba1q61
      write(23,259) ba1q62
 258  format('    -e "s/%sbstax/BA1Q6 = ',f9.5,' k;/g" %ret')
 259  format('    -e "s/%sbstbx/BA1Q6 = ',f9.5,' k;/g" %ret')
      endif

      if (ba1q71.eq.ba1q72) then
      write(23,160)
      write(23,161)
 160  format('    -e "s/%sbstay//g" %ret')
 161  format('    -e "s/%sbstby//g" %ret')
      else
      write(23,260) ba1q71
      write(23,261) ba1q72
 260  format('    -e "s/%sbstay/BA1Q7 = ',f9.5,' k;/g" %ret')
 261  format('    -e "s/%sbstby/BA1Q7 = ',f9.5,' k;/g" %ret')
      endif

      if (sc1.eq.sc2) then
      write(23,162)
      write(23,163)
 162  format('    -e "s/%sbstae//g" %ret')
 163  format('    -e "s/%sbstbe//g" %ret')
      else
      if (sc1.eq.1) then
      write(23,262)
      write(23,263)
 262  format('    -e "s/%sbstae/sc-T/g" %ret')
 263  format('    -e "s/%sbstbe/sc-F/g" %ret')
      else
      write(23,362)
      write(23,363)
 362  format('    -e "s/%sbstae/sc-F/g" %ret')
 363  format('    -e "s/%sbstbe/sc-T/g" %ret')
      endif
      endif

      if (msc1.eq.msc2) then
      write(23,164)
      write(23,165)
 164  format('    -e "s/%sbstaz//g" %ret')
 165  format('    -e "s/%sbstbz//g" %ret')
      else
      if (msc1.eq.1) then
      write(23,264)
      write(23,265)
 264  format('    -e "s/%sbstaz/msc-T/g" %ret')
 265  format('    -e "s/%sbstbz/msc-F/g" %ret')
      else
      write(23,364)
      write(23,365)
 364  format('    -e "s/%sbstaz/msc-F/g" %ret')
 365  format('    -e "s/%sbstbz/msc-T/g" %ret')
      endif
      endif

      write(23,333)
      write(23,444)

 333  format('    -e "s/%sub3/${input3}/g" %ret')
 444  format('    -e "s/%sub4/${input4}/g" %ret')

      write(23,1111)

 1111 format('       > ../gpastra_${input1}_${input2}.txt')

      write(23,*) ' '

      write(23,14)

 14   format('cat merge_${input1}_mask2.tex | %ret')

      write(23,555) run1
      write(23,666) run2

      write(23,333)
      write(23,444)

      write(23,2222)

 777  format(i3,' 'i3,' 'f5.2,' 'f5.3,' 'f5.3,' 'f6.2,' 'f5.1,' 'f6.2,
     &f5.1,' 'f6.3,' 'f6.3,' 'f6.3,' 'i4,' 'i1,' 'f9.5,' 'f9.5,' '
     &f9.5,' 'f9.5,' 'f9.5,' 'f9.5,' 'f9.5,' 'f9.5,' 'f9.5,' 'f9.5,' '
     &f9.5,' 'f9.5,' 'f9.5,' 'f9.5,' 'f9.5,' 'f9.5,' 'f9.5,' 'f9.5,' '
     &f9.5,' 'f9.5,' 'i1)

      write(24,777) run1, mp1, pl1, ss1, ch1, gg1, gp1, l1g1, l1p1,
     &bcs1, l1s11, l1s21, end11, sc1, s02q11, s02q21, s02q31, s02q41,
     &c2vq11, c2vq21, c2vq31, vq11, vq21, vq31, vq41, vq51, vq61,
     &ba1q11, ba1q21, ba1q31, ba1q41, ba1q51, ba1q61, ba1q71, msc1

 2222 format('       > ../merge_${input1}_${input2}.tex')

c      else
c      write(*,*) ' '
c      write(*,*) 'it does not make too much sense to compare ASTRA'
c      write(*,*) 'runs that end in different places but your wish'
c      write(*,*) 'is my command ... :) some screens may be missing !'
c      endif

      end
