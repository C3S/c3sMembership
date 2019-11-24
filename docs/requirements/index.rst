##########################
Requirements Specification
##########################


The requirements specification is used to track the requirements of the
existing c3sMembership application as well as new requirements for future
development.

The approach and document structure are inspired by the book "Requirements
Engineering Fundamentals" by Chris Rupp and Klaus Pohl
(English ISBN 978-1-93753-877-4, German ISBN 978-3-86490-283-3).

Authors:

- Sarah Stoffels
- Markus Lorenz, mrks@lrnz.name
- Eva Bolten
- Christoph Scheid



============
Introduction
============


The application C3S Membership Administration (c3sMembership) is used to
manage members of the C3S SCE. It focuses on the automation and support of
business processes for membership application, accounting and others.

This documents covers the following perspectives:

- Business perspective: it describes the business processes in whose context
  the application is used
- Structural perspective: specification of data structures which the
  application deals with
- Functional perspective: the workflows which the application covers
- Behavioural perspective: the use cases

Quality Criteria of the Requirements Specification:

- Unambiguousness and consistency
- Clear and well-defined structure
- Changeability and extensibility
- Completeness
- Traceability of changes



====================
Requirements Sources
====================


The requirements are gathered from stakeholders, legal regulations and
existing documentation.

Stakeholders are the users of the application:

- Financial accounting: for working with membership applications, invoices,
  payments, analyses, working with certain membership data (e.g. adresses,
  date of entry, date of cancellation), generating of legally required
  membership list (§§ 30, 31, 32 [GenG]_)
- Cooperative members: for registering, receiving information and invoices

**TODO:** *Investigate existing documentation.*



=====
Risks
=====


The C3S Membership Administration application is already in production and
being used. The introduction of changes therefore requires extensive testing
to provide a high reliability. The potential damages through a loss of data
could be disastrous.



==============
System Context
==============


The system consists of a publicly accessible part for membership application
and a restricted area for administration.

Interfaces exist for importing and exporting data.

**TODO**: *elaborate.*



==================
Business Processes
==================


Business processes are the basis of the application. They would function with
pen and paper but shall be technically supported by the application.
Therefore, this chapter describes and explains the business processes from
which use cases and the majority of business and technical requirements can be
derived. The business processes themselves are independent from the technology
which helps living them.



---------------
Membership List
---------------


The membership list must be maintained (Art. 14(4) [EU_CR_1435_2003_SCE]_, § 30
[GenG]_). For each member is must contain the following attributes:

- For natural persons (§ 30 II 1 1. [GenG]_)

  - Family name,
  - Given name and
  - Postal address

- For legal bodies (§ 30 II 1 1. [GenG]_)

  - Company name and
  - Postal address

- For bodies of persons (§ 30 II 1 1. [GenG]_)

  - Either

    - Name and
    - Postal address of the body of persons

  - Or

    - Family names,
    - Given names and
    - Postal addresses of the members

- Number of shares (§ 30 II 1 2. [GenG]_)
- Date of acquisition of membership (§ 30 II 2 [GenG]_)
- Justifying facts of the acquisition of membership (§ 30 II 2 [GenG]_), e.g.
  decision of the administrative board
- Date of loss of membership (§ 30 II 1 3. [GenG]_)
- Justifying facts of the loss of membership (§ 30 II 2 [GenG]_), e.g.
  resignation, expulsion, death, bankruptcy

Documents which are related to the acquisition or loss of membership must be
kept for three years until the end of the year in which the loss of membership
became effective (§ 30 III [GenG]_).

Members and third parties with legitimate interest review the membership list
at the cooperative (§ 31 I 2 [GenG]_).

The register court can demand a copy of the membership list (§ 32 [GenG]_).



-------------------------
Acquisition of Membership
-------------------------


The acquisition of membership must be approved by the administrative board
(art. 14(1) [EU_CR_1435_2003_SCE]_).

- Only natural persons can become full members, legal bodies can only become
  investor members (§ 4 I, II [C3S_Statute]_).
- A signed and fully filled membership application is required
  (§ 4 III [C3S_Statute]_).
- The membership application must be admitted by the administrative board
  (§ 4 III [C3S_Statute]_).
- The acquisiton of at least one share is required for becoming a member (§ 5 II
  1 [C3S_Statute]_) or the transfer of at least one share from an existing
  member (§ 5 II 1 [C3S_Statute]_, § 9 [C3S_Statute]_).
- The share must be paid for acquiring membership (§ 5 I 2 [C3S_Statute]_).
- A member can sign up to 60 shares (§ 5 II 2 [C3S_Statute]_).
- The nominal value of one share is 50 € (§ 5 I 1 [C3S_Statute]_).
- The acquisition of shares must be documented in the membership list no later
  than in the month following that in which the acquisition occurred (Art. 14(5)
  [EU_CR_1435_2003_SCE]_).
- Documents which are the foundation for entering members into the membership
  list must be kept for three years after the member lost membership (§ 30 III
  [GenG]_).

**TODO:**

- *Clarification of legal rules and regulations including the C3S statue which
  motivate the process.*
- *The decision of the administrative board must be recorded on the member's
  record in the membership list.*



------------------
Loss of Membership
------------------


The loss of shares must be documented in the membership list no later than in
the month following that in which the loss occurred (Art. 14(5)
[EU_CR_1435_2003_SCE]_).



Upon Resignation
================


Membership shall be lost upon resignation (art. 15(1) [EU_CR_1435_2003_SCE]_).

A member can resign from the C3S membership (§ 65 I [GenG]_, § 8
[C3S_Statute]_). The following criteria must be met:

- The member must deliver a written and signed membership resignation
  statement (§ 65 II 1 [GenG]_, § 8 I 1 [C3S_Statute]_).

Implications of the membership resignation are:

- The resignation becomes effective at the end of the following fiscal year
  (§ 8 I 2 [C3S_Statute]_, § 65 II [GenG]_).
- In extraordinary situations the resignation can become effective at the end
  of the fiscal year three months after the resignation statement if the
  ordinary notice period is unreasonable in the personal and economic
  circumstances of the member (§ 65 III [GenG]_).
- All mandatory and voluntary shares are terminated when the resignation
  becomes effective (§ 8 I 3 [C3S_Statute]_).
- The reimbursement value of signed shares depends on the decision of the
  administrative board before drawing the balance sheet (§ 22 III
  [C3S_Statute]_).
- Outstanding membership fees can be subtracted from the shares' reimbursement
  value.
- The date when the membership resignation becomes effective must be recoreded
  in the membership list and the member must be notified about this event
  immediately (§ 69 [GenG]_).

**TODO:**

- *Describe the business process.*
- *§ 67a [GenG]_*



Upon Expulsion
==============


Membership shall be lost upon expulsion where the member commits a serious
breach of his/her obligations or acts contrary to the interests of the SCE
(art. 15(1) [EU_CR_1435_2003_SCE]_).

**TODO:** *Describe the business process.*



Upon Transfer of All Shares
===========================


Membership shall be lost upon the transfer of all shares held to a member or a
natural person or legal entity which has acquired membership (art. 15(1)
[EU_CR_1435_2003_SCE]_, § 4 IV c [C3S_Statute]_).

In case a member transfers all shares the membership is lost without the
necessity to go through the process of winding up membership (§ 76 I 1 [GenG]_).

The loss of membership upon the transfer of all shares must be reflected in the
membership list (§ 76 III [GenG]_, § 69 [GenG]_).

**TODO:** *Elaborate.*



Upon Winding-up
===============


Membership shall be lost upon winding-up in the case of a member that is not a
natural person (Art. 15(1) [EU_CR_1435_2003_SCE]_, § 77a [GenG]_, § 4 IV d
[C3S_Statute]_).



Upon Death
==========


Membership shall be lost upon death (art. 15(1) [EU_CR_1435_2003_SCE]_, § 77
[GenG]_, § 4 IV d [C3S_Statute]_).

**TODO:** *Elaborate.*



Upon Bankruptcy
===============


Membership shall be lost upon bankruptcy (art. 15(1) [EU_CR_1435_2003_SCE]_, §§
66a, 77a [GenG]_, § 4 IV d [C3S_Statute]_).

**TODO:** *Elaborate.*



-------------------
Shares Transactions
-------------------



Acquisition of Additional Shares
================================


A member can acquire additional shares. The number of shares must be at most 60
(§ 5 II 2 [C3S_Statute]_, § 7a I [GenG]_).

The member must provide a signed and unconditional request for acquiring
additional shares (§ 15b I 1 [GenG]_).

The additional acquisition of shares is only allowed when all previously
acquired shares have been paid (§ 15b II [GenG]_).

The administrative board needs to approve the additional acquisition of shares
(Art. 4(11) [EU_CR_1435_2003_SCE]_, § 15b III 1 [GenG]_).

The acquisition of shares must be documented in the membership list no later than in
the month following that in which the acquisition occurred (Art. 14(5)
[EU_CR_1435_2003_SCE]_).

**TODO:** *Clarification of legal rules and regulations including the C3S
statue which motivate the process.*



Shares Transfer
===============


Shares can be transferred from one member to another member.

Requirements for transferring shares:

- Any number of shares which the member owns can be transferred (§ 9
  [C3S_Statute]_).

  - The member must transfer at least one share.
  - The member must transfer at most all shares in posession.
  - The acquirer must have in total not more than 60 shares after the transfer
    (§ 76 V [GenG]_).
  - If the member transfers all shares in posession then the membership is lost
    upon transfer of all shares.

- Consent of the administrative board is required for the transfer to become
  valid (§ 9 [C3S_Statute]_).
- A written statement of the transferring member signed by the giving must be
  given (§ 76 I 1 [GenG]_). **TODO:** *Must the acquiring member sign the
  statement? Compare § 76 I 1 [GenG]_ "durch schriftliche Vereinbarung". The
  term "Vereinbarung" (engl. agreement) probably implies a document signed by
  both parties of the shares transfer.*
- The date and number of shares of the shares transfer as well as the number of
  remaining shares must be immediately documented in the membership list (§ 69
  [GenG]_).
- The member must be immediately informed about the fact that the shares
  transfer was documented in the membership list (§ 69 [GenG]_).
- The acquirer of the shares must be a member or must become a member (§ 9
  [C3S_Statute]_).

  - A share transfer can be initiated from a member to an acquirer which is not
    a members yet but has already applied for membership.
  - The share transfer to an acquirer which is not a member yet can only be
    completed once the membership application of the acquirer was successful.
  - Acquirers which are not members yet do not have to acquire shares of their
    own if they are transferred at least one share from a member.

- The transfer of shares must be documented in the membership list no later
  than in the month following that in which the transfer occurred (Art. 14(5)
  [EU_CR_1435_2003_SCE]_).



Shares Termination
==================


A member can terminate all shares except the mandatory within the same notice
period as for a membership resignation (§ 67b [GenG]_). The following criteria
must be met:

- The member must deliver a written and signed shares termination statement
  (§ 67b I 1 [GenG]_).

Implications of the shares termination are:

- The notice period is one year at the end of the fiscal year (§ 8 I 2, 3
  [C3S_Statute]_, § 65 II [GenG]_).
- In extraordinary situations the termination can become effective at the end
  of the fiscal year three months after the termination statement if the
  ordinary notice period is unreasonable in the personal and economic
  circumstances of the member (§ 65 III [GenG]_).
- The reimbursement value of signed shares depends on the decision of the
  administrative board before drawing the balance sheet (§ 22 III
  [C3S_Statute]_).
- The date when the shares termination becomes effective must be recorded in the
  membership list and the member must be notified about this event and the
  number of remaining shares immediately (§ 69 [GenG]_).
- Transfer of all shares is a membership resignation (§ 4 IV c [C3S_Statute]_).
- The termination of shares must be documented in the membership list no later
  than in the month following that in which the termination occurred (Art. 14(5)
  [EU_CR_1435_2003_SCE]_).

**TODO:**

- *Describe the business process.*



----------------------
Membership Certificate
----------------------


Members are provided with a membership certificate and states:

- Member information

  - Last name
  - First name
  - Postal address
  - Membership number
  - Number of signed shares
  - Membership registration date

- C3S information

  - Official C3S name
  - Address
  - Email addess
  - URL
  - Court of law
  - Registration number
  - Name of the chairperson of the administrative board
  - Names of executive directors
  - Images of executive directors' signatures

Legal requirements:

- A member can request a copy of its own entry of the membership list (§ 31 I 2
  [GenG]_q).

**TODO:** *Legal requirements?*



Certificate Issuance
====================


The membership certificate must be created and sent to the member.
Certificates might be issued to a member more than once.
The certificate must contain the member's current information.

We supply the member with a URL which is valid for two weeks.
This link is sent per automated mail by request of the member to headquarters office.




C3S Information Changes
=======================


All changes to the C3S information must be adjusted in the certificate template.



------------------------------
Invitation to General Assembly
------------------------------


Legal requirements:

- The SCE shall hold a general meeting at least once each calendar year within
  six months of the end of its financial year (Art. 54(1)
  [EU_CR_1435_2003_SCE]_, § 48 I 3 [GenG]_, § 13 III 1 [C3S_Statute]_).
- The administrative board convenes the general assembly (Art. 54(2)
  [EU_CR_1435_2003_SCE]_, § 44 I [GenG]_, § 13 II 1 [C3S_Statute]_).
- All persons who are eligible to participate are direcly informed by the
  administrative board (Art. 56(1) [EU_CR_1435_2003_SCE]_, § 13 II 1
  [C3S_Statute]_). **TODO:** *"The general assembly is convened [...] by
  directly informing all persons who are eligible to participate, or by means of
  a notice in the form required in § 25 [...]" (§ 13 II 1 [C3S_Statute]_). This
  could mean that the publication via Musikforum could be sufficient and that
  the direct information sent to all members is not necessary.*
- The notice period for a general assembly is 30 days between the date of
  dispatch of the notice and the date of the opening of the general assembly
  (Art. 56(3) [EU_CR_1435_2003_SCE]_, § 13 II 1 [C3S_Statute]_).
- In urgent cases the notice period can be reduced to 15 days (Art. 56(3)
  [EU_CR_1435_2003_SCE]_, § 13 II 1 [C3S_Statute]_).
- Each full member has the right to attend the general assembly and take part in
  its decision-making process (§ 7 I c [C3S_Statute]_).
- Each non-user member has the right to attend the general assembly as an
  observer (§ 7 II a [C3S_Statute]_).
- The notice must contain (Art. 56(2) [EU_CR_1435_2003_SCE]_):

  - the name and registered office of the SCE,
  - the venue, date and time of the meeing,
  - where appropriate, the type of the general meeting,
  - the agenda, indicating the subjects to be discussed and the proposals for
    decisions.

Business requirements:

- All members must be invited to the annual general assembly.
- An individual invitation email containing details about the general assembly
  is sent to all members.
- All full and non-user members maintaining membership at the date on which the
  invitation is sent shall receive it. Even entities which lose membership after
  the date on which the invitations are sent but before the general assembly is
  held shall be invited because the loss of membership could be revised.
- The application must keep track about which email is sent to which member.
- There can be more than one general assembly per year.
- The application must handle email bounces and report them.
- Invitation text


  - The invitation text must be specified in the language of the SCE.
  - The invitation text can be specified in additional language.
  - If the invitation text is specified in additional languages then a default
    language must be set determining the language chosen for members for which
    a matching language is not present.

**TODO:** *Are members informed about the general assembly which gain membership
after the invitations are sent out but before the assembly is held? How?*



--------------------------
Annual Financial Statement
--------------------------


The annual financial statement (§ 33 I 2 [GenG]_) must be provided which
requires information about member payments such as the payment and
reimbursement of shares as well as membership fees.

**TODO:** *Elaborate.*



=========
Use Cases
=========


This section describes the uses cases for this application.
These use cases are derived from the business processes
as the application is used to support them.



-------------------------
Membership Administration
-------------------------


**TODO:** *Elaborate.*



Application for Membership Through a Web Interface
==================================================


**TODO:** *Elaborate.*



Handle and Approve a Membership Application
===========================================


**TODO:** *Elaborate.*



--------------------
Financial Accounting
--------------------


**TODO:** *Elaborate.*



Accounting
==========






Invoicing
=========


A list of all invoice must be accessible via the backend administration
interface. Furthermore, the invoices created for a member must be listed on the
members's detail page.



Create an Invoice
-----------------


Invoices are created as PDF files.

The amount of the invoice is booked on the invoicing account as well as the
invoicee's account.

An invoice which was created once must never be changed. For auditing purposes
neither the database entry nor the PDF file must be changed. The PDF file must
be archived.



Send an Invoice Email
---------------------


Sending the invoice means sending a link for a PDF download.

Due to legal requirements it is necessary that the invoice PDF can only be
accessed via a user login consisting of username and password.

According to the legal opinion of the C3S lawyers it is not sufficient for legal
requirements to send invoice links which contain a random token which cannot be
guessed. This legal opinion is based on the sentence of the Federal Court of
Justice (Bundesgerichtshof, BGH):

    Der Schutzbereich des Art. 10 Abs. 1 GG ist schon deshalb nicht berührt,
    weil das öffentliche Angebot von Dateien zum Download und auch der Zugriff
    darauf keine von dieser Vorschrift geschützte Individualkommunikation
    darstellt. Dass der Zugriff auf ein öffentliches Angebot zum Download
    jeweils mittels indi-vidueller technischer Kommunikationsverbindungen
    erfolgt, rechtfertigt die Ein-stufung als Kommunikation im Sinne des Art. 10
    Abs. 1 GG nicht, weil eine blo-ße technische Kommunikation nicht die
    spezifischen Gefahren für die Privatheit der Kommunikation aufweist, die
    diese Vorschrift schützt (vgl. Durner, ZUM 2010, 833, 840 f.). Ein solcher
    Zugriff stellt sich vielmehr als öffentliche, der Nutzung von Massenmedien
    vergleichbare Kommunikationsform dar, die von anderen Grundrechten -
    insbesondere Art. 5 Abs. 1 Satz 1 GG - erfasst wird (vgl. Billmeier aaO S.
    183).

    [BGH_I_ZR_3_14]_

This basically means that providing a file via a link which can be used by
anyone who knows it is not considered individual but public communication and is
therefore not sufficient for deliverying invoices to individuals.

The username and password on the other hand are considered private information.
Therefore, downloading a file from an internal login area which to access
requires the knowledge of the private username and the password is considered
private communication.

The aspect that this argument does not examine the or show any differences
between the knowledge of a link including an adequate random token and the
knowedge of a password is not changing the fact that it represents a currently
(as of August 2016) legally binding sentence of the Federal Court of Justice and
must therefore be followed.



Resend an Invoice Email
-----------------------


The accountant must be able to resend an invoice email. The email address to
which the new invoice email is sent must be the invoicee's current email address
which might have changed since the invoice was created.

The button for resending an invoice email must be presented next to the invoice
when it is listed in the global invoices list as well as the member's detail
page. A dialog must be confirmed to resend an invoice email after pushing the
button.

The invoice link of the resent invoice email must point to the same invoice PDF
file which was sent the first time.



Cancel an Invoice
-----------------


Invoices can be cancelled. In this case a cancelation invoice is created which
reverses the cancelled invoice. An invoice email for the cancelation email must
be sent to the invoicee.



Payments
========


**TODO:** *Elaborate.*



Enter a Payment
---------------


It is possible to enter payments on member's accounts.



Membership Dues
===============


The C3S can demand a membership fee:

- The dues amount can be calculated by a formula.
- The dues calculation formula can change each year.
- Dues amounts can be reduced.
- Dues might only apply to full members and not to investing members.
- Investing members can receive a request for donation instead of an invoice.
- Membership dues can be discounted. In this case the previous dues invoice is
  cancelled and a new invoice is created with the discounted dues amount.
- There are accounts for membership dues.

The account hierarchy for membership dues is as follows.

Root/Membership Dues/[YYYY]

- Invoicing

  - Invoiced
  - Cancelled

- Payment

  - Paid
  - Refunded



=====================
Business Requirements
=====================


Categorization according to the Kano modell [Wiki_Kano]_.



---------------
Must-be Quality
---------------


- Privacy. Personally identifiable information is processed.
- Data security. Personally identifiable information is processed.
- Data integrity and consistency.
- Usability of the graphical user interface (GUI).



-----------------------
One-dimensional Quality
-----------------------


**TODO:** *Elaborate.*



--------------------
Indifference Quality
--------------------


**TODO:** *Elaborate.*



---------------
Reverse Quality
---------------


**TODO:** *Elaborate.*



Membership Administration
=========================


**TODO:** *Elaborate.*



Financial Accounting
====================


**TODO:** *Elaborate.*



======================
Technical Requirements
======================


**TODO:** *Explain what technical requirements are.*



------------------
System Environment
------------------


The c3sMembership application will operate on a linux-server. The company-wide
currently used server-systems are based on the Debian Wheezy operating system.
The application deployment will be realized via a graphical web interface,
which can be used by a common browser. Therefore, the c3sMembership
application will run on a web server. The web server to use is not prescribed
by the server system or the IT-department.



--------------------
Software Environment
--------------------


A particular software environment is not prescribed by the server system or
IT-department, but a decision, to use Python as programming language and the
Pyramid framework was already mady by the development team. This decision was
based on already existing company software, the developer team's expertise and
the focus on a maximally customizable and robust open-source environment.
Therefore [Pyramid]_ will be used as framework for the server-side development
of the graphical interfaces, web-services and application logic.



======================
Quality Requiremements
======================


- Privacy and data security for preventing unauthorized access to and
  tampering of sensible data. Priority 1.
- Reliability and data consistency supported by a proper data model. Priority
  1.
- Usability
- Scalability, extensibility, maintainability
- Performance in terms of possible large data volumes in the future
