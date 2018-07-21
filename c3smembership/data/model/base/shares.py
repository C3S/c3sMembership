# -*- coding: utf-8  -*-
"""
Shares
"""

from datetime import date

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Integer,
    Unicode,
)

from c3smembership.data.model.base import Base


class Shares(Base):
    """
    A package of shares which a member acquires.

    Each shares package consists of one to sixty shares. One member may own
    several packages, e.g. from membership application, crowdfunding and
    requesting the acquisition of additional shares.

    Shares packages only come to existence once the business process is finished
    and the transaction is completed. Information about ongoing processes cannot
    here.
    """
    __tablename__ = 'shares'
    # pylint: disable=invalid-name
    id = Column(Integer, primary_key=True)
    """Technical primary key of the shares package."""
    number = Column(Integer())
    """Number of shares of the shares package."""
    date_of_acquisition = Column(Date(), nullable=False)
    """Date of acquisition of the shares package, i.e. the date of approval of
    the administrative board."""
    reference_code = Column(Unicode(255), unique=True)
    """A reference code used for email confirmation and as bank transfer
    purpose."""
    signature_received = Column(Boolean, default=False)
    """Flag indicating whether the signed application for becoming a member or
    acquiring additional shares was received."""
    signature_received_date = Column(
        Date(), default=date(1970, 1, 1))
    """Date on which the signed application for becoming a member or acquiring
    additional sharess was received."""
    signature_confirmed = Column(Boolean, default=False)
    """Flag indicating whether the confirmation email about the arrival of the
    signed application was sent."""
    signature_confirmed_date = Column(
        Date(), default=date(1970, 1, 1))
    """Date on which the confirmation email about the arrival of the signed
    application was sent."""
    payment_received = Column(Boolean, default=False)
    """Flag indicating whether the payment for the shares package was
    received."""
    payment_received_date = Column(
        Date(), default=date(1970, 1, 1))
    """Date on which the payment for the shares package was received."""
    payment_confirmed = Column(Boolean, default=False)
    """Flag indicating whether the confirmation email about the arrival of the
    payment was sent."""
    payment_confirmed_date = Column(
        Date(), default=date(1970, 1, 1))
    """Date on which the confirmation email about the arrival of the payment was
    sent."""
    accountant_comment = Column(Unicode(255))
    """A free text comment for accounting purposes."""
