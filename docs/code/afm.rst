.. _code_docs_afm:


Application for Membership (afm)
--------------------------------

Users can use the join form to supply their details.
Once they do that and submit the form,
a second page shows the data supplied for proofreading.
If all is correct and confirmed by the user,
a third view sends an email to the user.

That email has a link (containing a unique token) the user must use
which will take her to another view,
thereby confirming her email address.
This view asks for the password supplied through the initial form.

If all information matches (including the password)
the user is given her PDF for download.

A user must both

- print her PDF, sign it and send it to headquarters
- transfer the money for the shares aquired

to make her application valid so the board of directors may approve it.

Staff will notice both newly sent forms with signatures and
transfers to the C3S bank account and 'check' the relevant data fields
in the backend. Once these two checks are complete,
the board of directors may approve the person (or legal entity)
to become member.

Staff can then transmogrify the application into a real membership.


.. COMMENT add this to digraph users to make it LEFT-TO-RIGHT: rankdir=LR;

.. graphviz:: 

   digraph users {
      "yes.c3s.cc: join_c3s" -> "show_success" -> "success_check_email";
      "show_success" -> "yes.c3s.cc: join_c3s" [style=dotted,label="for corrections"];
      "success_check_email" -> "success_verify_email" [style=dotted,label="via link in email"];
      "success_verify_email" -> "show_success_pdf";
   }
