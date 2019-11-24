---------------
C3S-certificate
---------------

This repository holds 'private' files for membership certificate generation
in the c3sMembership webapp @ https://yes.c3s.cc.

* membership certificate generation
* invoice (and reversal invoice) generation

Private means non-public -- files we don't want to go into a public repository,
because this would enable anyone to create our very own certificates.

clone into c3sMembership/certificate. you might have to empty that folder first,
as it holds a README from the c3sMembership repo, so git will refuse to clone into that folder.


membership certificates
-----------------------

* urkunde_header_de.tex
* urkunde_header_en.tex
* urkunde_footer_de.tex
* urkunde_footer_en.tex
* Urkunde_Hintergrund.pdf (old, outdated)
* Urkunde_Hintergrund_EN.pdf (old, outdated)
* Urkunde_Hintergrund_blank.pdf
* sign_julian.png
* sign_meik.png


invoice generation
------------------

* C3S_briefkopf.lco
* C3S_briefkopf_2016.lco
* C3S_briefkopf_2017.lco

* dues15_invoice_de_v0.2.tex
* dues15_invoice_en_v0.2.tex
* dues15_storno_de_v0.1.tex
* dues15_storno_en_v0.1.tex

* dues16_invoice_de.tex
* dues16_invoice_en.tex
* dues16_storno_de.tex
* dues16_storno_en.tex

* dues17_invoice_de.tex
* dues17_invoice_en.tex
* dues17_storno_de.tex
* dues17_storno_en.tex



Preconditions
-------------

you need some packages installed in you system for pdflatex to work:
::

   $ apt-get install texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra texlive-lang-german pgf texlive-luatex
