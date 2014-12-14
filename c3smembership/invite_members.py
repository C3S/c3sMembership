# -*- coding: utf-8 -*-
from c3smembership.models import (
    C3sMember,
    #DBSession,
)
from datetime import datetime
import deform
from pkg_resources import resource_filename
from pyramid.i18n import (
    get_localizer,
)
#from pyramid.request import Request
#from pyramid.response import Response
from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message
from pyramid.view import view_config
from pyramid.threadlocal import get_current_request
from pyramid.httpexceptions import HTTPFound
#from pyramid.security import (
#    authenticated_userid,
    #forget,
    #remember,
#)
#from pyramid.url import route_url

#from pyramid_mailer import get_mailer
#from pyramid_mailer.message import Message
from translationstring import TranslationStringFactory
from types import NoneType
#import unicodecsv

deform_templates = resource_filename('deform', 'templates')
c3smembership_templates = resource_filename(
    'c3smembership', 'templates')

my_search_path = (deform_templates, c3smembership_templates)

_ = TranslationStringFactory('c3smembership')


def translator(term):
    return get_localizer(get_current_request()).translate(term)

my_template_dir = resource_filename('c3smembership', 'templates/')
deform_template_dir = resource_filename('deform', 'templates/')

zpt_renderer = deform.ZPTRendererFactory(
    [
        my_template_dir,
        deform_template_dir,
    ],
    translator=translator,
)
# the zpt_renderer above is referred to within the demo.ini file by dotted name

DEBUG = False
LOGGING = True

if LOGGING:  # pragma: no cover
    import logging
    log = logging.getLogger(__name__)


@view_config(permission='manage',
             route_name='invite_member')
def invite_member_BCGV(request):
    '''
    send email to member with link to ticketing
    '''
    mid = request.matchdict['m_id']
    _m = C3sMember.get_by_id(mid)
    if isinstance(_m, NoneType):
        request.session.flash(
            'id not found. no mail sent.',
            'messages')
        return HTTPFound(request.route_url('dashboard',
                                           number=request.cookies['on_page'],
                                           order=request.cookies['order'],
                                           orderby=request.cookies['orderby']))

    #import random
    #import string
    #_looong_token = u''.join(
    #    random.choice(
    #        string.ascii_uppercase + string.digits) for x in range(13))
    _url = (request.registry.settings['ticketing.url'] +
            '/lu/' + _m.email_confirm_code +
            '/' + _m.email)

    _body = u'''[english version below]

Hallo {1} {2},

der Verwaltungsrat der

Cultural Commons Collecting Society SCE
mit beschränkter Haftung
- C3S SCE -
Heyestraße 194
40625 Düsseldorf

lädt Dich ein

* zur 1. ordentlichen Generalversammlung nach § 13 der Satzung der C3S
  SCE [1],
* zum C3S-Barcamp 2014 und
* zur C3S-Party.

Bitte lies zunächst den gesamten Einladungstext. Er enthält wichtige
Hinweise.


Die Generalversammlung
======================

Die erste Generalversammlung der C3S SCE findet statt im Rahmen der
c/o pop convention in Köln:

am     23. August 2014
von    14:00 bis 18:00 Uhr (Verlängerung möglich)
im     Millowitsch-Theater, Aachener Straße 5, 50674 Köln

Die Anmeldung beginnt um 12:00 Uhr im Foyer des Millowitsch-Theaters.

Bitte komme zeitig, um Verzögerungen zu vermeiden, da wir Dir erst
Material aushändigen müssen. Die Teilnahme ist selbstverständlich
kostenlos. Bitte teile uns möglichst bis zum 11.08.2014 über dieses
Formular mit, ob Du teilnimmst oder nicht:

{0}


Warum ist Deine Teilnahme wichtig?
==================================

Die Generalversammlung ist das Organ, das die grundlegenden
Entscheidungen der C3S SCE trifft. Gemeinsam mit den anderen Mitgliedern
bist Du die Generalversammlung.

Eines unserer Hauptziele ist die Mitbestimmung durch alle Urheber_innen
und ausübenden Musiker_innen, und die Mitwirkung aller Mitglieder. Du
kannst Deine Meinung sagen, Du kannst diskutieren, Du kannst aktiver
Teil der C3S SCE werden, und Du kannst abstimmen. Vor allem kannst Du
Dich informieren, woran und wie die C3S SCE arbeitet, und Du kannst
andere Mitglieder kennenlernen. Die C3S SCE ist Deine Community,
Deine Genossenschaft. Nach der Zulassung wird sie Deine
Verwertungsgesellschaft sein.


Veranstaltungen: Ablauf und Rahmenprogramm
==========================================

21.08.2014: [c/o pop convention] "C3S SCE - Der Verwaltungsrat
            steht Rede und Antwort"
            Fritz Thyssen Stiftung / Robert Ellscheid Saal [2]
            Apostelnkloster 13-15, 50672 Köln
            14:30 - 15:30 Uhr
            Tickets zur c/o pop sind bei uns zum vergünstigten Preis
            von € 50 erhältlich (bitte Mail an office@c3s.cc senden).

22.08.2014: [C3S SCE] Barcamp 2014 [3]
            Alter Bahnhof Düsseldorf-Gerresheim [4]
            Heyestr. 194, 40625 Düsseldorf
            12:00 - 20:00 Uhr
            Teilnahme € 9,00 // Teilnahme inkl. Essen € 21,00
            Voranmeldung erforderlich:
            {0}

23.08.2014: [C3S SCE] 1. Generalversammlung der C3S SCE
            Millowitsch-Theater [5]
            Aachener Straße 5, 50674 Köln
            14:00 - 18:00 Uhr (Verlängerung möglich)
            Akkreditierung ab 12:00 Uhr
            Eintritt frei
            Voranmeldung erforderlich:
            {0}

23.08.2014: [C3S SCE] Party mit DJ - offen für alle
            CAMPI Volksbühne (neben Millowitsch-Theater)
            Aachener Straße 5, 50674 Köln
            ab 17:00 Uhr
            Eintritt frei


Agenda der Generalversammlung 2014 der C3S SCE
==============================================

Begrüßung der Anwesenden

# 1 Bestimmen der Versammlungsleitung und de(s/r) Protokollführer(s/in)

# 2 Genehmigung der Tagesordnung

# 3 Wiederkehrende Tagesordnungspunkte

## 3.1 Entgegennahme der Tätigkeitsberichte der geschäftsführenden
       Direktoren und des Verwaltungsrates mit anschließender Aussprache
## 3.2 Feststellung des Jahresabschlusses
## 3.3 Entscheidung über die Verwendung des Jahresüberschusses und die
       Verrechnung des Jahresfehlbetrages
## 3.4 Entlastung der geschäftsführenden Direktoren und des
       Verwaltungsrates

# 4 Anträge auf Satzungsänderung
Zurzeit liegen uns keine Anträge auf Satzungsänderung vor.

# 5 Bericht vom C3S-Barcamp 2014

# 6 Antrag auf Beschluss zur Einrichtung eines Beirats

# 7 Einrichtung der Beratungskommissionen
## 7.1 Kommission Tarife
## 7.2 Kommission Verteilung
## 7.3 Kommission Wahrnehmungsverträge
## 7.4 Kommission Mitgliederausbau
## 7.5 Kommission Mitgliedsbeitragsordnung

# 8 Diskussionen

Beschlussanträge und Anträge zur Änderung der Tagesordnung kannst Du bis
zum 16. August (Ausschlussfrist 24 Uhr MESZ/CEST, d.h. UTC +2) in
Textform unter agenda@c3s.cc einreichen.


Organisatorisches
=================


Teilnahme
---------
Teilnahmeberechtigt an der Generalversammlung sind nur Mitglieder der
C3S SCE oder Bevollmächtigte nicht anwesender Mitglieder.


Stellvertretende Bevollmächtigte
--------------------------------
Falls eine Satzungsänderung beantragt wird, müssen mindestens 50% der
stimmberechtigten Mitglieder vertreten sein (§ 13 Abs. 4 Satz 2 der
Satzung). Solltest Du nicht teilnehmen können und stimmberechtigt sein,
also nutzendes Mitglied, erteile bitte eine Vollmacht:

https://url.c3s.cc/vmprivat

Bitte bedenke, dass jede(r) Bevollmächtigte nur zwei Mitglieder per
Vollmacht vertreten darf. Frage also vorher nach, ob der/die
Bevollmächtigte schon andere Personen vertritt. Vollmachten müssen
schriftlich und im Original vorgelegt werden; Fax oder Scan reichen
nicht aus!

Bevollmächtigte dürfen nach § 13 (6), Satz 3 der Satzung nur
Mitglieder der Genossenschaft, Ehegatten, Eltern, Kinder oder
Geschwister eines Mitglieds sein. Eingetragene Lebenspartner werden wie
Ehegatten behandelt. Du kannst online bei Absage Deiner Teilnahme
eine(n) Vertreter(in) benennen - mehr dazu unter:

{0}

Bitte denke daran, dass der/die Bevollmächtigte die von Dir
unterzeichnete schriftliche Vollmacht mitbringen muss. Einen Vordruck
für die Vollmacht findest Du hier:

Privatpersonen: https://url.c3s.cc/vmprivat
Unternehmen & Vereinigungen: https://url.c3s.cc/vmkoerperschaft

Auch nicht-stimmberechtigte, investierende Mitglieder können sich
vertreten lassen.


Geschäftsbericht
----------------
Am 17.08.2014 erhältst Du den Geschäftsbericht sowie eine detaillierte
Agenda mit allen Anträgen auf Satzungsänderung und Beschlussanträgen
zum Download. Auf der Basis der Informationen im Geschäftsbericht
entscheidet die Generalversammlung über die Entlastung des
Verwaltungsrats und der Geschäftsführenden Direktoren.


Barcamp
-------
Um die Generalversammlung vorzubereiten und Diskussionen vorzuverlagern,
werden wir am 22. August ein Barcamp [2] in Düsseldorf organisieren.
Eine Zusammenfassung der Ergebnisse des Barcamps wird Dir bei der
Anmeldung zur Generalversammlung ausgehändigt. Themen, die dort
besprochen werden sollen, kannst Du hier im Wiki einsehen und ergänzen:

https://url.c3s.cc/barcamp2014

Die Anzahl der Teilnehmer am Barcamp ist aus Kapazitätsgründen
beschränkt auf 200 Personen. Daher bitte frühzeitig anmelden - ab
11. August 2014 ist keine Anmeldung mehr möglich. Tagestickets sind
nicht verfügbar!


Audio-Protokoll
---------------
Während der Generalversammlung wird ein Audio-Mitschnitt aufgezeichnet,
um ein fehlerfreies Protokoll zu gewährleisten. Der Mitschnitt wird
nicht veröffentlicht, aber intern als Anhang zum Protokoll archiviert.

Wer nicht möchte, dass sein Redebeitrag aufgezeichnet wird, kann dem vor
Beginn seines/ihres Beitrags widersprechen.


OpenPGP Key-Signing-Party
-------------------------
Wenn Du bereits Deine E-Mails mit OpenPGP verschlüsselst, kannst Du nach
Ende der Generalversammlung die Party zum gegenseitigen Key-Signing
nutzen. Alle Infos dazu findest Du in Kürze im Wiki:

https://url.c3s.cc/keysigning


Anreise und Unterbringung
-------------------------
Leider können wir als C3S SCE keine Anreisen oder Unterbringung selber
organisieren oder finanzieren. Wir können Dir aber helfen, indem Du eine
Mitfahrgelegenheit oder Couchsurfing anbieten oder danach fragen kannst:

Mitfahrgelegenheiten:   https://url.c3s.cc/fahren
Couchsurfing:           https://url.c3s.cc/schlafen


Wo gehts zur Anmeldung?
=======================

Dies ist Dein individueller Link zur Anmeldung:


***************************  W I C H T I G  ***************************

  {0}

Bitte teile uns dort rechtzeitig mit, ob Du teilnnimmst. Wir müssen
umgehend wissen, ob die Location ausreichend groß ist. Wenn irgend
möglich, antworte uns daher bitte bis zum 11. August 2014.

***********************************************************************

Auf der verlinkten Seite kannst Du separat die Teilnahme für die
Generalversammlung und das Barcamp bestätigen. Auch Essen und
(natürlich) ein T-Shirt mit neuem Motiv für die tollen C3S-Tage am Rhein
kannst Du Dir holen - die T-Shirt-Preise haben wir für die
Veranstaltungen übrigens heruntergesetzt. 

Wenn Du sicher sein möchtest, von Deiner Teilnahme an Barcamp oder
Generalversammlung ein T-Shirt mit nach Hause zu nehmen, solltest Du es
unbedingt bis zum 11. August 2014 vorbestellen. Danach ist aus
organisatorischen Gründen keine Vorbestellung mehr möglich. Wir werden
nur einzelne Restposten zum Verkauf anbieten können.


Das wars! Versorge uns mit Themenvorschlägen, plane Deine Fahrt - dann
sehen wir uns Ende August in Düsseldorf und Köln! Bei Fragen kannst Du
Dich wie immer an info@c3s.cc wenden oder auch unsere neue
Xing-Community nutzen:

https://url.c3s.cc/xing


Wir freuen uns auf Dich & Deine Ideen!

Der Verwaltungsrat der C3S SCE
Meinhard Starostik - Vorsitzender


====================

Der Verwaltungsrat der C3S SCE setzt sich zusammen aus:

Geschäftsführende Direktoren:
* m.eik michalke (Kulturpolitik)
* Wolfgang Senges (Geschäftsentwicklung & Partnerschaften)

Vorsitz:
Meinhard Starostik, Vorsitzender des VR (Wirtschaftsrecht & Rechnungswesen)
Danny Bruder, stellv. Vorsitzender des VR (Netzwerk Kunst & Kultur)

Weitere Mitglieder:
* Tanja Mark (Marketing & PR)
* Florian Posdziech (Schriftführer des VR // Webentwicklung)
* Christoph Scheid (Technologie)
* Sven Scholz (Kommunikation)
* Holger Schwetter (Finanzierung & Forschung)
* Michael Weller (Urheberrecht)
* Veit Winkler (Interne Organisation & Internationalisierung)

====================

Links:

[1] Satzung der C3S SCE: https://url.c3s.cc/satzung
[2] Karte Fritz Thyssen Stiftung: https://url.c3s.cc/fritzthyssen
[3] Was ist ein Barcamp? https://url.c3s.cc/bcerklaerung
[4] Karte C3S HQ (Barcamp): https://url.c3s.cc/c3shq
[5] Karte Millowitsch-Theater (Generalversammlung):
https://url.c3s.cc/millowitsch
[6] Karte CAMPI Volksbühne (Party): https://url.c3s.cc/campi

++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++++++++++++++++++++++++

Hello {1} {2},

the board of directors of the

Cultural Commons Collecting Society SCE
mit beschränkter Haftung
- C3S SCE -
Heyestraße 194
40625 Düsseldorf
Germany

invites you

* to the 1. statutory general assembly, according to § 13 of the
  articles of association of the C3S SCE [1],
* to the C3S barcamp 2014,
* to the C3S party.

Please read the whole text of the invitation. It contains important
information.


The general assembly
====================

The first general assembly of the C3S SCE will be held in the context of
the c/o pop convention in Cologne

on     23rd August 2014
from   2 pm to 6 pm (extension possible)
at     Millowitsch Theater, Aachener Straße 5, 50674 Köln

Registration will commence at 12 noon in the foyer of the Millowitsch
Theater.

Please be punctual in order to avoid delays, because there is material
to be distributed to you. Of course, participation is free. If possible,
please let us know until August 11th, 2014, via this form, whether you
will attend or not:

{0}


Why is it important that you participate?
=========================================

The general assembly is the body that takes the fundamental decisions
for the C3S. You are the general assembly, together with the other members.

One of our main objectives is the co-determination exercised by all user
members, and the participation of all members. You can voice your
opinions, you can become an active part of the C3S SCE, and you can
vote. Most of all, you can catch up on information about how the C3S SCE
operates, and what it is currently engaged with, and you can get to know
other members. The C3S SCE is your community, your cooperative. Once it
has been approved, it will be your collecting society.


Events: Agenda and supporting program
=====================================

21st August 2014: [c/o pop convention] "C3S SCE - The board of directors
                  answers your questions"
                  Fritz Thyssen Stiftung / Robert Ellscheid Saal [2]
                  Apostelnkloster 13-15, 50672 Köln
                  2:30 pm - 3:30 pm
                  Tickets for the c/o pop are available at a discount
                  rate of € 50 (please send an e-mail to office@c3s.cc).

22nd August 2014: [C3S SCE] Barcamp 2014 [3]
                  Alter Bahnhof Düsseldorf-Gerresheim [4]
                  Heyestraße. 194, 40625 Düsseldorf
                  12:00 am - 8:00 pm
                  Participation € 9,00 // Participation and food € 21,00
                  Advance reservation required:
                  {0}

23rd August 2014: [C3S SCE] 1. General Assembly of the C3S SCE
                  Millowitsch Theater [5]
                  Aachener Straße 5, 50674 Köln
                  2:00 pm - 6:00 pm (extension possible)
                  Accrediting commences at 12:00 am
                  Admission free // Food sold by CAMPI
                  Advance reservation required:
                  {0}

23rd August 2014: [C3S SCE] Party with DJ - open for all
                  CAMPI Volksbühne (next to the Millowitsch Theater)
                  Aachener Straße 5, 50674 Köln
                  from 5:00 pm
                  Admission free


Agenda of the general assembly 2014 of the C3S SCE
==================================================

Welcoming address

# 1 Appointment of the chairperson of the assembly
    and the keeper of the minutes

# 2 Approval of the agenda

# 3 Recurring items on the agenda

## 3.1 Acceptance of the progress report of the executive directors and
       the board of directors, followed by debate
## 3.2 Approval of the annual report
## 3.3 Decision on the use of the annual net profit and the accounting
       for the annual deficit
## 3.4 Discharge of the executive directors and the board of directors

# 4 Proposals for amendments to the articles of association
Currently, there are no proposals for ammendments.

# 5 Report from the C3S barcamp 2014

# 6 Proposal for the resolution to establish an advisory board

# 7 Establishment of the advisory commissions
## 7.1 Tariff commission
## 7.2 Distribution commission
## 7.3 Contracts commission
## 7.4 Membership development commission
## 7.5 Fees schedule commission

# 8 Discussions

You are entitled to contribute resolution proposals and proposals for
amendments to the agenda until August 16th, 2014 (deadline: 12 pm
midnight MEST/CEST, that is UTC +2) by sending them in written form
to agenda@c3s.cc.


Organizational information
==========================

Participation
-------------
Entitled to participate in the general assembly are C3S members only or
the authorized representatives of absent members.

Authorized representatives
--------------------------
In case changes in the articles of association are announced, at least
50% of the total number of registered members entitled to vote have to
be present or represented (§ 13 Abs. 4 Satz 2 der Satzung). If you are
not able to attend but you are entitled to vote, please choose a
proxy who has to produce a written power of attorney for registration:

https://url.c3s.cc/auprivate

Please consider, no proxy may represent more than two members.
Therefore, you should ask your representative if he or she represents
other members as well. We accept the original document only; we can’t
accept a fax or scan!

According to § 13 (6), sentence 3, of the articles of association, only
members of the cooperative, their spouses, parents, children or siblings
are allowed to become authorized representatives of absent members.
Registered civil partners are treated as spouses. If you cancel your
participation, you may register a representative online -- read more at:

{0}

Please make sure that your representative brings a written
authorization signed by you. One representative may represent no more
than two members with voting power. You can find a blank form for the
authorization here:

Private persons: https://url.c3s.cc/auprivate
Corporations & associations: https://url.c3s.cc/aucorporate

Also, members who are not entitled to vote (investing members) may
choose a proxy.


Annual report
-------------
By 17th August, 2014, you will receive the annual report and the
detailed agenda for download. Based on the information in the annual
report, the general assembly will decide about the discharge of the
executive directors and the board of directors.

BarCamp
-------
In order to prepare the general assembly and to shift forward
discussions, we will organize a barcamp [2] in Düsseldorf on August
22nd. You will receive a summary of the results of the barcamp when you
are accredited for the general assembly. Here you may read, and add to,
the topics that are to be discussed during the barcamp:

https://url.c3s.cc/barcamp2014

The number of participants at the BarCamp is limited to 200 persons for
capacity reasons. It’s worth to register early - from August 11th,
2014, no registrations will be possible anymore. There is no sale of
tickets at the door!

Audio recording
---------------
An audio recording of the general assembly will be made in order to
ensure error-free minutes. The recording will not be published, but
archived internally as an appendix to the minutes.

Those who do not wish their speech contributions to be recorded, may
veto before commencing to speak.


OpenPGP Key-Signing-Party
-------------------------

If you already use OpenPGP to encrypt your e-mails you may take the
opportunity for a round of key-signing after the assembly. More
information will be available soon in our wiki:

https://url.c3s.cc/keysigning


Travel and accommodation
------------------------

Unfortunately, the C3S SCE is unable to organize, or finance, travel and
accommodation. But we can help you if you want to offer, or search for,
a lift or a couchsurfing place:

Lifts:         https://url.c3s.cc/lifts
Couchsurfing:  https://url.c3s.cc/sleep


Where do I register?
====================

This is your personal registration link:


*********************** I M P O R T A N T ***********************

  {0}

Please let us know in time whether you will participate. We must know as
soon as possible whether the location will be large enough. If possible,
please respond by August 11th, 2014, at the latest.

*****************************************************************

On the linked page you can confirm your participation in the general
assembly and the barcamp separately. You can also book food, and (of
course) a t-shirt with a new image for the great days with the C3S on
the banks of the river Rhine -- we have reduced our t-shirt prices for
these events. 

If you want to be sure to take a t-shirt home from either the BarCamp or
the general assembly, save the date for pre-order: 11th August, 2014.
For organizational reasons, there is no pre-order possible from then on.
On location, we will only be able to sell the last few remaining items.

That's all! Let us know your proposals for topics, plan your trip -- and
we shall meet at the end of August in Düsseldorf and Cologne! If you
have questions, you can get in touch, as always, via info@c3s.cc, or use
our brand-new Xing community (English is welcome):

https://url.c3s.cc/xing


We are looking forward to seeing you and learning to know your ideas!

The board of directors of the C3S SCE
Meinhard Starostik - Chairman


====================

The board of directors of the C3S SCE is:

Executive Directors:
* m.eik michalke (Cultural Politics)
* Wolfgang Senges (Business Development & Partnerships)

Chairmen:
Meinhard Starostik, Chairman (Business Law & Accounting)
Danny Bruder, stellv. Vorsitzender des VR (Network Artists & Culture)

Further members of the board:
* Tanja Mark (Marketing & PR)
* Florian Posdziech (Web Development)
* Christoph Scheid (Technology)
* Sven Scholz (Communikation)
* Holger Schwetter (Finance & Research)
* Michael Weller (Copyright)
* Veit Winkler (Internal Management & Internationalization)

====================

Links:

[1] Articles of association of the C3S SCE: https://url.c3s.cc/statutes
[2] Map of Fritz Thyssen Stiftung: https://url.c3s.cc/fritzthyssen
[3] What is a barcamp? https://url.c3s.cc/bcexplanation
[4] Map of C3S HQ (Barcamp): https://url.c3s.cc/c3shq
[5] Map of Millowitsch Theater (General Assembly):
    https://url.c3s.cc/millowitsch
[6] Map of CAMPI Volksbühne (Party): https://url.c3s.cc/campi
'''.format(
        _url,  # {0}
        _m.firstname,  # {1}
        _m.lastname,  # {2}
    )

    log.info("mailing event invitation to to AFM # %s" % _m.id)

    message = Message(
        subject=(u'[C3S] Invitation to Barcamp and Assembly '
                 u'/ Einladung zu Barcamp und Generalversammlung'),
        sender='yes@office.c3s.cc',
        recipients=[_m.email],
        body=_body,
        extra_headers={
            'Reply-To': 'yes@c3s.cc',
            }
    )
    #print(message.subject)
    #print(message.body)
    mailer = get_mailer(request)
    mailer.send(message)
    #_m._token = _looong_token
    _m.email_invite_flag_bcgv14 = True
    _m.email_invite_date_bcgv14 = datetime.now()
    return HTTPFound(request.route_url('dashboard',
                                       number=request.cookies['on_page'],
                                       order=request.cookies['order'],
                                       orderby=request.cookies['orderby']) +
                     '#member_' + str(_m.id))