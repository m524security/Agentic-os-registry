"""Model-independent web tools (standard library only): fetch, search, bounded crawl.

These run on the host, so any model - cloud or a small local one - can use web content as retrieved
context. Page text is untrusted data. Private/loopback addresses are refused unless WEB_ALLOW_PRIVATE=1.
Search needs a SearXNG-style JSON endpoint in SEARCH_URL (self-hostable); nothing is bundled.
"""
import ipaddress, json, os, re, socket, time, urllib.error, urllib.parse, urllib.request, urllib.robotparser
from html.parser import HTMLParser

UA = 'AgenticOS-Registry/0.5 (+local agent tool)'
TEXT_TYPES = ('text/html', 'text/plain', 'application/xhtml+xml', 'application/json', 'text/xml', 'application/xml')

class WebError(Exception):
    pass

def check_url(url):
    p = urllib.parse.urlparse(url)
    if p.scheme not in ('http', 'https') or not p.hostname:
        raise WebError('Only http(s) URLs are allowed')
    if os.environ.get('WEB_ALLOW_PRIVATE') == '1':
        return url
    try:
        addrs = {ai[4][0] for ai in socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == 'https' else 80))}
    except OSError:
        raise WebError('Host does not resolve')
    for a in addrs:
        ip = ipaddress.ip_address(a.split('%')[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise WebError('Private or local address refused (set WEB_ALLOW_PRIVATE=1 to allow)')
    return url

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None

class _Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts, self.links, self.title, self._skip, self._in_title = [], [], '', 0, False
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript', 'svg'): self._skip += 1
        if tag == 'title': self._in_title = True
        if tag == 'a':
            href = dict(attrs).get('href')
            if href: self.links.append(href)
        if tag in ('p', 'br', 'div', 'li', 'h1', 'h2', 'h3', 'tr'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript', 'svg') and self._skip: self._skip -= 1
        if tag == 'title': self._in_title = False
    def handle_data(self, data):
        if self._in_title: self.title += data
        elif not self._skip: self.parts.append(data)

def _get(url, timeout, max_bytes, hops=3):
    opener = urllib.request.build_opener(_NoRedirect)
    for _ in range(hops + 1):
        check_url(url)
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,text/plain,application/json;q=0.9,*/*;q=0.1'})
        try:
            with opener.open(req, timeout=timeout) as r:
                ctype = (r.headers.get('content-type') or '').split(';')[0].strip().lower()
                charset = r.headers.get_content_charset() or 'utf-8'
                if ctype and ctype not in TEXT_TYPES: raise WebError('Unsupported content type: ' + ctype)
                return r.status, ctype, r.read(max_bytes), url, charset
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and e.headers.get('Location'):
                url = urllib.parse.urljoin(url, e.headers['Location']); continue
            raise WebError('HTTP %d' % e.code)
        except (urllib.error.URLError, TimeoutError, OSError):
            raise WebError('Fetch failed')
    raise WebError('Too many redirects')

def fetch(url, timeout=15, max_bytes=500_000):
    status, ctype, data, final, charset = _get(url, timeout, max_bytes)
    try: body = data.decode(charset, 'replace')
    except LookupError: body = data.decode('utf-8', 'replace')
    if ctype in ('text/html', 'application/xhtml+xml', ''):
        p = _Text()
        try: p.feed(body)
        except Exception: pass
        text = re.sub(r'\n\s*\n+', '\n', re.sub(r'[ \t]+', ' ', ''.join(p.parts))).strip()
        return {'url': final, 'status': status, 'title': p.title.strip(), 'text': text,
                'links': [urllib.parse.urljoin(final, l).split('#')[0] for l in p.links]}
    return {'url': final, 'status': status, 'title': '', 'text': body.strip(), 'links': []}

def search(query, limit=5, timeout=20):
    base = os.environ.get('SEARCH_URL')
    if not base: raise WebError('SEARCH_URL is not set (point it at a SearXNG instance)')
    url = base.rstrip('/') + '/search?' + urllib.parse.urlencode({'q': query, 'format': 'json'})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=timeout) as r:
            data = json.loads(r.read(2_000_000))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise WebError('Search backend unreachable or returned invalid JSON')
    return [{'title': x.get('title', ''), 'url': x.get('url', ''), 'snippet': x.get('content', '')}
            for x in data.get('results', []) if x.get('url')][:limit]

def crawl(seed, max_pages=10, max_depth=1, delay=0.5, same_host=True, timeout=15):
    """Bounded, polite crawl: robots rules, visited set on normalized URLs, per-request delay, hard limits."""
    max_pages, max_depth = min(max_pages, 50), min(max_depth, 3)
    host = urllib.parse.urlparse(seed).netloc
    robots, pages, skipped, seen = {}, [], [], set()
    queue, stop = [(seed, 0)], 'queue_exhausted'
    def allowed(u):
        pu = urllib.parse.urlparse(u); key = pu.scheme + '://' + pu.netloc
        if key not in robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                _, _, data, _, _ = _get(key + '/robots.txt', timeout, 100_000); rp.parse(data.decode('utf-8', 'replace').splitlines())
            except WebError:
                rp.parse([])
            robots[key] = rp
        return robots[key].can_fetch(UA, u)
    while queue:
        if len(pages) >= max_pages: stop = 'max_pages'; break
        url, depth = queue.pop(0)
        norm = urllib.parse.urldefrag(url)[0].rstrip('/')
        if norm in seen: continue
        seen.add(norm)
        if same_host and urllib.parse.urlparse(url).netloc != host: skipped.append({'url': url, 'reason': 'other host'}); continue
        try:
            if not allowed(url): skipped.append({'url': url, 'reason': 'robots.txt'}); continue
            page = fetch(url, timeout=timeout)
        except WebError as e:
            skipped.append({'url': url, 'reason': str(e)}); continue
        pages.append({'url': page['url'], 'title': page['title'], 'text': page['text'], 'depth': depth, 'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
        if depth < max_depth: queue += [(l, depth + 1) for l in page['links'] if l.startswith('http')]
        time.sleep(delay)
    return {'pages': pages, 'skipped': skipped[:50], 'stop_reason': stop, 'limits': {'max_pages': max_pages, 'max_depth': max_depth}}
