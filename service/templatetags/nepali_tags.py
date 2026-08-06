from datetime import date, datetime
from django import template
from service.nepali_date import (
    ad_to_bs_display,
    ad_to_bs,
    format_bs_date,
    bs_fiscal_year,
    bs_fiscal_year_nepali,
    to_nepali_digits,
)

register = template.Library()


@register.filter(name="to_bs")
def to_bs(value, include_year=True):
    if not value:
        return "—"
    return ad_to_bs_display(value, include_year=include_year)


@register.filter(name="to_bs_nepali")
def to_bs_nepali(value):
    if not value:
        return "—"
    try:
        bs_y, bs_m, bs_d = ad_to_bs(value)
        bs_str = format_bs_date(bs_y, bs_m, bs_d)
        return to_nepali_digits(bs_str)
    except Exception:
        return str(value)


@register.filter(name="bs_fy")
def bs_fy(value):
    if not value:
        return "—"
    try:
        return bs_fiscal_year(value)
    except Exception:
        return "—"


@register.simple_tag
def current_bs_date():
    return ad_to_bs_display(date.today())
