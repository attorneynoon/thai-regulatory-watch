"""Validate the observed, public AMLO enter-site form before a bounded POST.

This is deliberately not a generic form submission or authentication adapter.
The caller retains Transport's robots, destination, TLS and response checks.
"""
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .registry import allowed_url

AMLO_ENTRY='https://www.amlo.go.th/index.php/th/'
AMLO_FIELDS={'intro_page':'1'}


def validate_public_form(source, body, final_url):
    """Return only the exact observed public navigation field, or fail closed."""
    expected=source.get('public_form_url')
    configured=source.get('public_form')
    if expected!=AMLO_ENTRY or configured!=AMLO_FIELDS:
        raise ValueError('Unsupported public navigation form contract')
    expected=allowed_url(expected,source['allowed_hosts'])
    if allowed_url(final_url,source['allowed_hosts'])!=expected:
        raise ValueError('Public navigation form page changed destination')
    soup=BeautifulSoup(body,'html.parser')
    matched=[]
    for form in soup.find_all('form'):
        if str(form.get('method','get')).lower()!='post':
            continue
        try:
            action=allowed_url(urljoin(final_url,form.get('action','')),source['allowed_hosts'])
        except ValueError:
            continue
        if action==expected:
            matched.append(form)
    if len(matched)!=1:
        raise ValueError('Expected one exact public navigation form')
    fields={}
    for control in matched[0].select('input[name], button[name], select[name], textarea[name]'):
        name=control.get('name')
        if control.name!='input' or control.get('type','text').lower()!='hidden' or control.has_attr('disabled') or name in fields:
            raise ValueError('Unexpected public navigation form control')
        fields[name]=control.get('value')
    if fields!=configured:
        raise ValueError('Public navigation form fields changed')
    return dict(fields)
