Routes of the Application
-------------------------

Routes in Pyramid are URL-path-patterns to match incoming web requests
to view functions. Each route has a name.

The routes can be configured in several ways. In c3sMembership
the routes are declared in the main method (in __init__.py),
so this configuration is applied during app instanatiation.

.. list-table:: List of Routes and Patterns
   :widths: 30 30 30
   :header-rows: 1

   * - Name (route name)
     - Pattern (URL path)
     - see (view code)
   * - join
     - /
     - :ref:`code_docs_afm`
   * - static
     - /static/
     - :ref:`code_docs_init_main`



One of Pyramids convenience functions is to show the routes configured
in the running app.
This can be seen through-the-web during development,
if the developers toolbar is active. 
(do not use this feature on production systems!)

If you have installed the project locally,
you can get the info through the *proutes* command:


The raw output from *proutes*:
::

   Name            Pattern                        View                     
   ----            -------                        ----                     
   __static_deform/ /static_deform/*subpath        <function <pyramid.static.static_view object at 0x7f7b89b3cb10> at 0x7f7b8976f230>
   __static/       /static/*subpath               <function <pyramid.static.static_view object at 0x7f7b89b3cc50> at 0x7f7b8976f410>
   join            /                              <function join_c3s at 0x7f7b8967a758>
   success         /success                       <function show_success at 0x7f7b8967a848>
   success_check_email /check_email                   <function success_check_email at 0x7f7b8967ab18>
   verify_email_password /verify/{email}/{code}         <function success_verify_email at 0x7f7b8967ac80>
   success_pdf     /C3S_SCE_AFM_{namepart}.pdf    <function show_success_pdf at 0x7f7b8967a9b0>
   verify_afm_email /vae/{refcode}/{token}/{email} <function verify_mailaddress_conf at 0x7f7b8972dc08>
   dashboard_only  /dashboard                     <function dashboard_only at 0x7f7b8971d140>
   dashboard       /dashboard/{number}/{orderby}/{order} <function accountants_desk at 0x7f7b89796cf8>
   dash            /dash/{number}/{orderby}/{order} None                     
   toolbox         /toolbox                       <function toolbox at 0x7f7b8972daa0>
   stats           /stats                         <function stats_view at 0x7f7b8967a230>
   staff           /staff                         <function staff_view at 0x7f7b8972d848>
   new_member      /new_member                    <function new_member at 0x7f7b89672230>
   detail          /detail/{memberid}             <function member_detail at 0x7f7b89724488>
   edit            /edit/{_id}                    <function edit_member at 0x7f7b896c4de8>
   switch_sig      /switch_sig/{memberid}         <function switch_sig at 0x7f7b89724b90>
   mail_sig_confirmation /mail_sig_conf/{memberid}      <function mail_signature_confirmation at 0x7f7b8971df50>
   regenerate_pdf  /re_C3S_SCE_AFM_{code}.pdf     <function regenerate_pdf at 0x7f7b897246e0>
   switch_pay      /switch_pay/{memberid}         <function switch_pay at 0x7f7b89724938>
   mail_pay_confirmation /mail_pay_conf/{memberid}      <function mail_payment_confirmation at 0x7f7b8971daa0>
   mail_mail_confirmation /mail_mail_conf/{memberid}     <function mail_mail_conf at 0x7f7b8972d0c8>
   mail_sig_reminder /mail_sig_reminder/{memberid}  <function mail_signature_reminder at 0x7f7b89724230>
   mail_pay_reminder /mail_pay_reminder/{memberid}  <function mail_payment_reminder at 0x7f7b8971dcf8>
   delete_entry    /delete/{memberid}             <function delete_entry at 0x7f7b8971d398>
   delete_afms     /delete_afms                   <function delete_afms at 0x7f7b89724de8>
   login           /login                         <function accountants_login at 0x7f7b89796e60>
   recover_password /recover_password              <function recover_password at 0x7f7b89672398>
   export_all      /export_all                    <function export_db at 0x7f7b896d3c80>
   export_members  /export_members                <function export_memberships at 0x7f7b896d3ed8>
   export_yes_emails /export_yes_emails             <function export_yes_emails at 0x7f7b896da1b8>
   import_all      /import_all                    <function import_db at 0x7f7b896da410>
   import_with_ids /import_with_ids               <function import_db_with_ids at 0x7f7b896da668>
   import_founders /import_founders               <function import_founders at 0x7f7b896d3a28>
   import_crowdfunders /import_crowdfunders           <function import_crowdfunders at 0x7f7b896d37d0>
   fix_import_crowdfunders /fix_import_crowdfunders       <function fix_import_crowdfunders at 0x7f7b896d3578>
   logout          /logout                        <function logout_view at 0x7f7b8971d848>
   mail_mtype_form /mtype/{afmid}                 <function mail_mtype_fixer_link at 0x7f7b8972d320>
   mtype_form      /mtype/{refcode}/{token}/{email} <function membership_status_fixer at 0x7f7b8972d488>
   mtype_thanks    /mtype_thanks                  <function membership_status_thanks at 0x7f7b8972d578>
   afms_awaiting_approval /afms_awaiting_approval        <function afms_awaiting_approval at 0x7f7b896c4b90>
   flag_duplicates /flag_dup                      <function flag_duplicates at 0x7f7b89660500>
   merge_duplicates /merge_dup                     <function merge_duplicates at 0x7f7b8966acf8>
   make_member     /make_member/{afm_id}          <function make_member_view at 0x7f7b89660c08>
   merge_member    /merge_member/{afm_id}/{mid}   <function merge_member_view at 0x7f7b8966af50>
   make_founders_members /make_founders_members         <function make_founders_members at 0x7f7b896609b0>
   make_crowdfounders_members /make_crowdfounders_members    <function make_crowdfounders_members at 0x7f7b89660758>
   make_yesser_members /make_yesser_members           <function make_yesser_members at 0x7f7b89660e60>
   membership_listing_backend_only /memberships                   <function membership_listing_backend at 0x7f7b8966aaa0>
   membership_listing_backend /memberships/{number}/{orderby}/{order} <function membership_listing_backend at 0x7f7b8966a848>
   membership_listing_alphabetical /aml                           <function member_list_print_view at 0x7f7b8966a5f0>
   membership_listing_date_pdf /aml-{date}.pdf                <function member_list_date_pdf_view at 0x7f7b8966a398>
   membership_listing_aufstockers /aml_aufstockers               <function member_list_aufstockers_view at 0x7f7b8966a140>
   plz_dist        /plz_dist                      <function plz_dist at 0x7f7b8967a5f0>
   members_by_postcode_DE /members_by_postcode_DE_{prefix}.png <function members_by_postcode at 0x7f7b8967a398>
   get_member      /members/{memberid}            <function get_member at 0x7f7b8971d5f0>
   shares_detail   /shares_detail/{id}            <function shares_detail at 0x7f7b89672cf8>
   shares_edit     /shares_edit/{id}              <function shares_edit at 0x7f7b89672f50>
   shares_delete   /shares_delete/{id}            <function shares_delete at 0x7f7b89672aa0>
   certificate_mail /cert_mail/{id}                <function send_certificate_email at 0x7f7b896602a8>
   certificate_pdf /cert/{id}/C3S_{name}_{token}.pdf <function generate_certificate at 0x7f7b896dad70>
   certificate_pdf_staff /cert/{id}/C3S_{name}.pdf      <function generate_certificate_staff at 0x7f7b89660050>
   annual_reporting /annual_reporting              <function annual_report at 0x7f7b8972de60>
   invite_member   /invite_member/{m_id}          <function invite_member_BCGV at 0x7f7b896dab18>
   invite_batch    /invite_batch/{number}         <function batch_invite at 0x7f7b896da8c0>
   search_people   /search_people                 <function search_people at 0x7f7b89672848>
   autocomplete_people_search /aps/                          <function autocomplete_people_search at 0x7f7b896c4938>
   search_codes    /search_codes                  <function search_codes at 0x7f7b896725f0>
   autocomplete_input_values /aiv/                          <function autocomplete_input_values at 0x7f7b896c46e0>
   fix_database    /fix_database                  <function fix_database at 0x7f7b896d30c8>
   fix_dob         /fix_dob                       <function fix_date_of_acquisition at 0x7f7b896d3320>
   member          /lm                            <pyramid.config.views.MultiView object at 0x7f7b89d2eb50>
