import base64
import calendar
import datetime
import re
import unicodedata
import warnings
from binascii import Error as BinasciiError
from email.utils import formatdate
from urllib.parse import (
    ParseResult, SplitResult, _coerce_args, _splitnetloc, _splitparams, quote,
    quote_plus, scheme_chars, unquote, unquote_plus,
    urlencode as original_urlencode, uses_params,
)

from django.core.exceptions import TooManyFieldsSent
from django.utils.datastructures import MultiValueDict
from django.utils.deprecation import RemovedInDjango40Warning
from django.utils.functional import keep_lazy_text

# based on RFC 7232, Appendix C
ETAG_MATCH = re.compile(r'''
    \A(      # start of string and capture group
    (?:W/)?  # optional weak indicator
    "        # opening quote
    [^"]*    # any sequence of non-quote characters
    "        # end quote
    )\Z      # end of string and capture group
''', re.X)

MONTHS = 'jan feb mar apr may jun jul aug sep oct nov dec'.split()
__D = r'(?P<day>\d{2})'
__D2 = r'(?P<day>[ \d]\d)'
__M = r'(?P<mon>\w{3})'
__Y = r'(?P<year>\d{4})'
__Y2 = r'(?P<year>\d{2})'
__T = r'(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})'
RFC1123_DATE = re.compile(r'^\w{3}, %s %s %s %s GMT$' % (__D, __M, __Y, __T))
RFC850_DATE = re.compile(r'^\w{6,9}, %s-%s-%s %s GMT$' % (__D, __M, __Y2, __T))
ASCTIME_DATE = re.compile(r'^\w{3} %s %s %s %s$' % (__M, __D2, __T, __Y))

RFC3986_GENDELIMS = ":/?#[]@"
RFC3986_SUBDELIMS = "!$&'()*+,;="

FIELDS_MATCH = re.compile('[&;]')


@keep_lazy_text
def urlquote(url, safe='/'):
    """
    A legacy compatibility wrapper to Python's urllib.parse.quote() function.
    (was used for unicode handling on Python 2)
    """
    warnings.warn(
        'django.utils.http.urlquote() is deprecated in favor of '
        'urllib.parse.quote().',
        RemovedInDjango40Warning, stacklevel=2,
    )
    return quote(url, safe)


@keep_lazy_text
def urlquote_plus(url, safe=''):
    """
    A legacy compatibility wrapper to Python's urllib.parse.quote_plus()
    function. (was used for unicode handling on Python 2)
    """
    warnings.warn(
        'django.utils.http.urlquote_plus() is deprecated in favor of '
        'urllib.parse.quote_plus(),',
        RemovedInDjango40Warning, stacklevel=2,
    )
    return quote_plus(url, safe)


@keep_lazy_text
def urlunquote(quoted_url):
    """
    A legacy compatibility wrapper to Python's urllib.parse.unquote() function.
    (was used for unicode handling on Python 2)
    """
    warnings.warn(
        'django.utils.http.urlunquote() is deprecated in favor of '
        'urllib.parse.unquote().',
        RemovedInDjango40Warning, stacklevel=2,
    )
    return unquote(quoted_url)


@keep_lazy_text
def urlunquote_plus(quoted_url):
    """
    A legacy compatibility wrapper to Python's urllib.parse.unquote_plus()
    function. (was used for unicode handling on Python 2)
    """
    warnings.warn(
        'django.utils.http.urlunquote_plus() is deprecated in favor of '
        'urllib.parse.unquote_plus().',
        RemovedInDjango40Warning, stacklevel=2,
    )
    return unquote_plus(quoted_url)


def urlencode(query, doseq=False, safe='', encoding=None, errors=None,
              quote_via=quote_plus):
    """
    A version of Python's urllib.parse.urlencode() function that can operate on
    MultiValueDict and other dictionary-like objects.

    The parameters are the same as the original except:
    * If the optional parameter 'doseq' is evaluates to True, individual key=value
      pairs separated by '&' are generated for each element of the value
      sequence for the key.  When a sequence of values is used, the effect
      varies by the value of the original_urlencode's 'safe' parameter:
      * Per PEP 3333, safe characters in the value aren't encoded. E.g.,
        urlencode([('key', 'val;ue')], safe=';') -> 'key=val;ue'
      * When a key is supplied, per PEP 3333, the key isn't encoded. E.g.,
        urlencode([('k;ey', 'value')]) -> 'k;ey=value'
    """
    if isinstance(query, MultiValueDict):
        query = query.lists()
    elif hasattr(query, 'items'):
        query = query.items()
    query_params = []
    for key, value in query:
        if isinstance(value, (list, tuple)):
            if doseq:
                for item in value:
                    query_params.append((key, item))
            else:
                query_params.append((key, value))
        else:
            query_params.append((key, value))
    return original_urlencode(
        query_params, doseq, safe, encoding, errors, quote_via
    )


def http_date(epoch_seconds=None):
    """
    Format the time to match the RFC1123 date format as specified by HTTP
    RFC7231 section 7.1.1.1.

    `epoch_seconds` is a floating point number expressed in seconds since the
    epoch, in UTC - such as that outputted by time.time(). If set to None, it
    defaults to the current time.

    Output a string in the format 'Wdy, DD Mon YYYY HH:MM:SS GMT'.
    """
    return formatdate(epoch_seconds, usegmt=True)


def parse_http_date(date):
    """
    Parse a date format as specified by HTTP RFC7231 section 7.1.1.1.

    The three formats allowed by the RFC are accepted, even if only the first
    one is still in widespread use.

    Return an integer expressed in seconds since the epoch, in UTC.
    """
    # email.utils.parsedate() does the job for RFC1123 dates; unfortunately
    # RFC7231 makes it mandatory to support RFC850 dates too. So we roll
    # our own RFC-compliant parsing.
    for regex in RFC1123_DATE, RFC850_DATE, ASCTIME_DATE:
        m = regex.match(date)
        if m is not None:
            break
    else:
        raise ValueError("%r is not in a valid HTTP date format" % date)
    try:
        tz = m.groupdict()
        mon = MONTHS.index(tz['mon'].lower()) + 1
        if 'year' in tz:
            year = int(tz['year'])
            # RFC 7231 section 7.1.1.1: 2-digit years should be interpreted
            # relative to current year, with preference for dates within 50 years
            if year < 100:
                current_year = datetime.datetime.now().year
                # Convert 2-digit year to 4-digit based on current year
                century = (current_year // 100) * 100
                full_year_current_century = century + year
                full_year_previous_century = century - 100 + year
                
                # Choose the century that puts the date closest to current year
                # but prefer past dates when equidistant
                diff_current = abs(full_year_current_century - current_year)
                diff_previous = abs(full_year_previous_century - current_year)
                
                if diff_previous < diff_current:
                    year = full_year_previous_century
                elif diff_current < diff_previous:
                    year = full_year_current_century
                else:
                    # Equidistant - prefer the past date
                    year = full_year_previous_century
        else:
            year = datetime.datetime.now().year
        day = int(tz['day'])
        hour = int(tz['hour'])
        min = int(tz['min'])
        sec = int(tz['sec'])
        result = datetime.datetime(year, mon, day, hour, min, sec)
        return calendar.timegm(result.timetuple())
    except (ValueError, OverflowError, OSError) as exc:
        raise ValueError('Invalid date %r (%r)' % (date, exc))


def parse_etags(etag_str):
    """
    Parse a string of ETags given in an If-None-Match or If-Match header as
    defined by RFC 7232. Return a list of quoted ETags, or ['*'] if all ETags
    should be matched.
    """
    if etag_str.strip() == '*':
        return ['*']
    else:
        # Parse each ETag individually to handle malformed headers.
        etag_matches = (ETAG_MATCH.match(etag.strip()) for etag in etag_str.split(','))
        return [match.group(1) for match in etag_matches if match]


def quote_etag(etag_str):
    """
    If the provided string is already a quoted ETag, return it. Otherwise, wrap
    the string in quotes, making it a strong ETag.
    """
    return etag_str if ETAG_MATCH.match(etag_str) else '"%s"' % etag_str


def parse_header_parameters(line):
    """
    Parse a Content-type like header.

    Return the main content-type and a dictionary containing
    options.
    """
    parts = line.split(';')
    main_type = parts.pop(0).strip()
    pdict = {}
    for p in parts:
        i = p.find('=')
        if i >= 0:
            name = p[:i].strip().lower()
            value = p[i + 1:].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
                value = value[1:-1]
                value = value.replace('\\\\', '\\')
                value = value.replace('\\"', '"')
            pdict[name] = value
    return main_type, pdict


def _parse_header_parameters(s):
    while s[:1] == ';':
        s = s[1:]
        end = s.find(';')
        while end > 0 and (s.count('"', 0, end) - s.count('\\"', 0, end)) % 2:
            end = s.find(';', end + 1)
        if end < 0:
            end = len(s)
        f = s[:end]
        yield f
        s = s[end:]


def parse_header_name(line):
    """Parse header name from a line."""
    return line.split(':', 1)[0].strip()


def is_same_domain(host, pattern):
    """
    Return ``True`` if the host is either an exact match or a match
    to the wildcard pattern.

    Any pattern beginning with a period matches a domain and all of its
    subdomains. (e.g. ``.example.com`` matches ``example.com`` and
    ``foo.example.com``). Anything else is an exact string match.
    """
    if not pattern:
        return False

    pattern = pattern.lower()
    return (
        pattern[0] == '.' and (host.endswith(pattern) or host == pattern[1:]) or
        pattern == host
    )


def url_has_allowed_host_and_scheme(url, allowed_hosts, require_https=False):
    """
    Return ``True`` if the url uses an allowed host and a safe scheme.

    Always return ``False`` on an empty url.

    If ``require_https`` is ``True``, only 'https' will be considered a valid
    scheme, as opposed to 'http' and 'https' with the default ``False``.

    Note: "True" doesn't entail that a URL is "safe". It may still be e.g.
    quoted incorrectly. Ensure to also use django.utils.encoding.iri_to_uri()
    on the path component of untrusted URLs.
    """
    if url is not None:
        url = url.strip()
    if not url:
        return False
    if allowed_hosts is None:
        allowed_hosts = set()
    elif isinstance(allowed_hosts, str):
        allowed_hosts = {allowed_hosts}
    # Chrome treats \ completely as / in paths but it could be part of some
    # basic auth credentials so we need to check both URLs.
    return (
        _url_has_allowed_host_and_scheme(url, allowed_hosts, require_https) and
        _url_has_allowed_host_and_scheme(url.replace('\\', '/'), allowed_hosts, require_https)
    )


def _url_has_allowed_host_and_scheme(url, allowed_hosts, require_https=False):
    # Chrome considers any URL with more than two slashes to be absolute, but
    # urlparse is not so flexible. Treat any url with three slashes as unsafe.
    if url.startswith('///'):
        return False
    try:
        url_info = _urlparse(url)
    except ValueError:  # e.g. invalid IPv6 URL
        return False
    # Forbid URLs like http:///example.com - with a scheme, but without a hostname.
    # In that URL, example.com is not the hostname but, a path component. However,
    # Chrome will still consider example.com to be the hostname, so we must not
    # allow this syntax.
    if not url_info.netloc and url_info.scheme:
        return False
    # Forbid URLs that start with control characters. Some browsers (like
    # Chrome) ignore quite a few control characters at the start of a
    # URL and might consider the URL as scheme relative.
    if unicodedata.category(url[0])[0] == 'C':
        return False
    scheme = url_info.scheme
    # Consider URLs without a scheme (e.g. //example.com/p) to be http.
    if not url_info.scheme and url_info.netloc:
        scheme = 'http'
    valid_schemes = ['https'] if require_https else ['http', 'https']
    return ((not url_info.netloc or any(
        is_same_domain(url_info.netloc, host) for host in allowed_hosts
    )) and (not scheme or scheme in valid_schemes))


def _urlparse(url, scheme='', allow_fragments=True):
    """Return a 6-tuple: (scheme, netloc, path, params, query, fragment)."""
    url, scheme, _coerce_result = _coerce_args(url, scheme)
    splitresult = _urlsplit(url, scheme, allow_fragments)
    scheme, netloc, url, query, fragment = splitresult
    if scheme in uses_params and ';' in url:
        url, params = _splitparams(url)
    else:
        params = ''
    result = ParseResult(scheme, netloc, url, params, query, fragment)
    return _coerce_result(result)


def _urlsplit(url, scheme='', allow_fragments=True):
    """Return a 5-tuple: (scheme, netloc, path, query, fragment)."""
    url, scheme, _coerce_result = _coerce_args(url, scheme)
    netloc = query = fragment = ''
    i = url.find(':')
    if i > 0:
        if url[:i] == 'http':  # optimize the common case
            scheme = url[:i].lower()
            url = url[i + 1:]
            if url[:2] == '//':
                netloc, url = _splitnetloc(url, 2)
                if (('[' in netloc and ']' not in netloc) or
                        (']' in netloc and '[' not in netloc)):
                    raise ValueError("Invalid IPv6 URL")
            if allow_fragments and '#' in url:
                url, fragment = url.split('#', 1)
            if '?' in url:
                url, query = url.split('?', 1)
        else:
            for c in url[:i]:
                if c not in scheme_chars:
                    break
            else:
                # make sure "url" is not actually a port number (in which case
                # "scheme" is really part of the path)
                rest = url[i + 1:]
                if not rest or any(c not in '0123456789' for c in rest):
                    # not a port number
                    scheme, url = url[:i].lower(), rest

    if url[:2] == '//':
        netloc, url = _splitnetloc(url, 2)
        if (('[' in netloc and ']' not in netloc) or
                (']' in netloc and '[' not in netloc)):
            raise ValueError("Invalid IPv6 URL")
    if allow_fragments and '#' in url:
        url, fragment = url.split('#', 1)
    if '?' in url:
        url, query = url.split('?', 1)
    v = SplitResult(scheme, netloc, url, query, fragment)
    return _coerce_result(v)


def escape_leading_slashes(url):
    """
    If redirecting to an absolute path (two leading slashes), a slash must be
    escaped to prevent browsers from handling the path as schemaless and
    redirecting to another host.
    """
    if url.startswith('//'):
        url = '/%2F' + url[2:]
    return url


def _parseparam(s):
    while s[:1] == ';':
        s = s[1:]
        end = s.find(';')
        while end > 0 and (s.count('"', 0, end) - s.count('\\"', 0, end)) % 2:
            end = s.find(';', end + 1)
        if end < 0:
            end = len(s)
        f = s[:end]
        yield f
        s = s[end:]


def parse_qsl(qs, keep_blank_values=False, strict_parsing=False,
              encoding='utf-8', errors='replace', max_num_fields=None,
              separator='&'):
    """
    Return a list of key/value tuples parsed from query string.

    Copied from urlparse with an additional "max_num_fields" argument.
    Copyright (C) 2013 Python Software Foundation (see LICENSE.python).

    Arguments:

    qs: percent-encoded query string to be parsed

    keep_blank_values: flag indicating whether blank values in
        percent-encoded queries should be treated as blank strings. A
        true value indicates that blanks should be retained as blank
        strings. The default false value indicates that blank values
        are to be ignored and treated as if they were  not included.

    strict_parsing: flag indicating what to do with parsing errors. If
        false (the default), errors are silently ignored. If true,
        errors raise a ValueError exception.

    encoding and errors: specify how to decode percent-encoded sequences
        into Unicode characters, as accepted by the bytes.decode() method.

    max_num_fields: int. If set, then throws a TooManyFieldsSent exception
        if there are more than max_num_fields fields parsed.

    separator: str. The symbol to use for separating the query arguments.
        Defaults to &.

    Returns a list, as G-d intended.
    """
    if max_num_fields is not None:
        num_fields = 1 + qs.count(separator)
        if max_num_fields < num_fields:
            raise TooManyFieldsSent(
                'The number of GET/POST parameters exceeded '
                'settings.DATA_UPLOAD_MAX_NUMBER_FIELDS.'
            )
    pairs = [s2 for s1 in qs.split(separator) for s2 in s1.split(';')]
    r = []
    for name_value in pairs:
        if not name_value and not strict_parsing:
            continue
        nv = name_value.split('=', 1)
        if len(nv) != 2:
            if strict_parsing:
                raise ValueError("bad query field: %r" % (name_value,))
            # Handle case of a control-name with no equal sign
            if keep_blank_values:
                nv.append('')
            else:
                continue
        if len(nv[1]) or keep_blank_values:
            name = nv[0].replace('+', ' ')
            name = unquote(name, encoding=encoding, errors=errors)
            value = nv[1].replace('+', ' ')
            value = unquote(value, encoding=encoding, errors=errors)
            r.append((name, value))
    return r


def limited_parse_qsl(qs, keep_blank_values=False, strict_parsing=False,
                      encoding='utf-8', errors='replace', max_num_fields=None,
                      separator='&'):
    """
    Return a list of key/value tuples parsed from query string.

    Similar to urllib.parse.parse_qsl, but with an additional "max_num_fields"
    argument and slightly different behavior.
    """
    if max_num_fields is not None:
        if max_num_fields <= 0:
            raise ValueError('max_num_fields must be a positive integer')
        # Use FIELDS_MATCH.split() which is equivalent to re.split('[&;]', qs)
        # but faster.
        fields = FIELDS_MATCH.split(qs)
        if len(fields) > max_num_fields:
            raise TooManyFieldsSent(
                'The number of GET/POST parameters exceeded '
                'settings.DATA_UPLOAD_MAX_NUMBER_FIELDS.'
            )
    else:
        fields = FIELDS_MATCH.split(qs)
    
    r = []
    for field in fields:
        if not field and not strict_parsing:
            continue
        if '=' in field:
            name, value = field.split('=', 1)
        else:
            if strict_parsing:
                raise ValueError("bad query field: %r" % (field,))
            if keep_blank_values:
                name, value = field, ''
            else:
                continue
        if value or keep_blank_values:
            name = name.replace('+', ' ')
            name = unquote(name, encoding=encoding, errors=errors)
            value = value.replace('+', ' ')
            value = unquote(value, encoding=encoding, errors=errors)
            r.append((name, value))
    return r


def base36_to_int(s):
    """
    Convert a base 36 string to an int. Raise ValueError if the input won't fit
    into an int.
    """
    # To prevent overconsumption of server resources, reject any
    # base36 string that is longer than 13 base36 digits (log_36(2^64))
    if len(s) > 13:
        raise ValueError("Base36 input too large")
    return int(s, 36)


def int_to_base36(i):
    """
    Convert an integer to a base36 string.
    """
    char_set = '0123456789abcdefghijklmnopqrstuvwxyz'
    if i < 0:
        raise ValueError("Negative base36 conversion input.")
    if i < 36:
        return char_set[i]
    b36 = ''
    while i != 0:
        i, n = divmod(i, 36)
        b36 = char_set[n] + b36
    return b36