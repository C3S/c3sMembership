from deform import widget
from colander import (
    null,
)

'''
this custom made widget needs to be patched into the deform widget.py
that came with you installation. the best place is between TextInputWidget
and MoneyInputWidget. you can find the widget.py in the virtualenv:
e.g. env/lib/python2.7/site-packages/deform-2.0a2-py2.7.egg/deform/widget.py
'''


class TextInputSliderWidget(widget.Widget):
    """
    Renders an ``<input type="text"/>`` widget
    accompanied by a div to show the slider.

    **Attributes/Arguments**

    size
        The size, in columns, of the text input field.  Defaults to
        ``None``, meaning that the ``size`` is not included in the
        widget output (uses browser default size).

    template
       The template name used to render the widget.  Default:
        ``textinput``.

    readonly_template
        The template name used to render the widget in read-only mode.
        Default: ``readonly/textinput``.

    strip
        If true, during deserialization, strip the value of leading
        and trailing whitespace (default ``True``).

    style
        A string that will be placed literally in a ``style`` attribute on
        the text input tag.  For example, 'width:150px;'.  Default: ``None``,
        meaning no style attribute will be added to the input tag.

    mask
        A :term:`jquery.maskedinput` input mask, as a string.

        a - Represents an alpha character (A-Z,a-z)
        9 - Represents a numeric character (0-9)
        * - Represents an alphanumeric character (A-Z,a-z,0-9)

        All other characters in the mask will be considered mask
        literals.

        Example masks:

          Date: 99/99/9999

          US Phone: (999) 999-9999

          US SSN: 999-99-9999

        When this option is used, the :term:`jquery.maskedinput`
        library must be loaded into the page serving the form for the
        mask argument to have any effect.  See :ref:`masked_input`.

    mask_placeholder
        The placeholder for required nonliteral elements when a mask
        is used.  Default: ``_`` (underscore).

    """
    template = 'slider'
    readonly_template = 'readonly/textinput'
    size = None
    strip = True
    mask = None
    mask_placeholder = "_"
    style = None
    requirements = (('jquery.maskedinput', None), )

    def serialize(self, field, cstruct, **kw):
        if cstruct in (null, None):
            cstruct = ''
        readonly = kw.get('readonly', self.readonly)
        template = readonly and self.readonly_template or self.template
        values = self.get_template_values(field, cstruct, kw)
        return field.renderer(template, **values)

    def deserialize(self, field, pstruct):
        if pstruct is null:
            return null
        if self.strip:
            pstruct = pstruct.strip()
        if not pstruct:
            return null
        return pstruct
