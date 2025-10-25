# Web Scraping Compliance Guide

This guide outlines the legal, ethical, and technical best practices for responsible web scraping implemented in this project.

## Table of Contents

1. [Legal Considerations](#legal-considerations)
2. [Ethical Guidelines](#ethical-guidelines)
3. [Technical Best Practices](#technical-best-practices)
4. [Implementation Guide](#implementation-guide)
5. [Monitoring and Auditing](#monitoring-and-auditing)
6. [Troubleshooting](#troubleshooting)

---

## Legal Considerations

### 1. **robots.txt Compliance**

**Status:** ✅ IMPLEMENTED

The `robots.txt` file is a legal and ethical standard that website owners use to communicate crawling permissions.

- **Requirement:** MUST check and respect robots.txt before scraping
- **Implementation:** `RobotsChecker` class in `src/scraping/robots_parser.py`
- **Legal Risk:** Ignoring robots.txt can violate:
  - Computer Fraud and Abuse Act (CFAA) in the US
  - Computer Misuse Act in the UK
  - Similar laws in other jurisdictions

**Example:**
```python
from src.scraping.robots_parser import RobotsChecker

checker = RobotsChecker(user_agent="YourBot/1.0")
if checker.can_fetch("https://example.com/page"):
    # Proceed with scraping
    pass
```

### 2. **Terms of Service (ToS)**

**Status:** ⚠️ MANUAL REVIEW REQUIRED

Many websites explicitly prohibit automated data collection in their Terms of Service.

**Actions Required:**
- Review the ToS of each target website
- Document your review and legal assessment
- Obtain explicit permission if ToS prohibits scraping
- Consider using official APIs when available

**High-Risk ToS Terms:**
- "No automated access"
- "Scraping prohibited"
- "API use only"
- "Commercial use restricted"

### 3. **Copyright and Database Rights**

**Legal Principles:**
- **Facts are not copyrightable**, but creative expression is
- **Database compilations** may have sui generis rights (EU)
- **Fair use/Fair dealing** may apply for research purposes

**Best Practices:**
- Scrape only publicly available data
- Don't copy creative content (descriptions, reviews, images)
- Focus on factual data (schedules, prices, dates)
- Add transformative value through analysis

### 4. **Personal Data Protection**

**Regulations:**
- GDPR (EU)
- CCPA (California)
- Other regional privacy laws

**Requirements:**
- Don't scrape personal information unless absolutely necessary
- If scraping personal data:
  - Document legal basis (legitimate interest, consent, etc.)
  - Implement data minimization
  - Provide privacy notice
  - Honor data subject rights (deletion, access, etc.)
  - Ensure secure storage

### 5. **Computer Fraud Laws**

**CFAA (US) and Similar Laws:**
- Don't circumvent technical barriers (login walls, CAPTCHAs)
- Don't cause damage or impairment to systems
- Don't exceed authorized access
- Respect rate limits and technical measures

---

## Ethical Guidelines

### 1. **Transparency**

**Status:** ✅ IMPLEMENTED

**Requirements:**
- Identify your bot clearly
- Provide contact information
- Be honest about your purpose

**Implementation:**
```python
user_agent = "OperaResearchBot/1.0 (+https://github.com/your-username/repo)"
```

The user agent includes:
- Bot name and version
- Contact URL/email in parentheses

### 2. **Respectful Rate Limiting**

**Status:** ✅ IMPLEMENTED

**Best Practices:**
- **Minimum 1-2 seconds between requests** to same domain
- **Respect Crawl-delay** directive in robots.txt
- **Limit concurrent requests** (typically 1-5 per domain)
- **Slow down during peak hours** when possible

**Implementation:**
```python
scraper = CompliantOperaScraper(
    user_agent="YourBot/1.0",
    contact_info="https://your-site.com/contact",
    requests_per_second=1.0,      # Max 1 request per second
    min_delay_seconds=2.0          # Minimum 2s delay
)
```

### 3. **Server Load Considerations**

**Guidelines:**
- Don't scrape during peak business hours
- Use caching to avoid redundant requests
- Monitor server response times
- Back off if you receive 429 (Too Many Requests) or 503 errors

### 4. **Attribution and Credit**

When publishing scraped data:
- Credit the source website
- Link back to original sources
- Don't claim data as your own
- Respect the website's reputation

---

## Technical Best Practices

### 1. **robots.txt Parsing**

**Implementation:** `src/scraping/robots_parser.py`

**Features:**
- Parses and respects robots.txt directives
- Caches robots.txt files (24-hour default)
- Checks Crawl-delay and Request-rate
- Handles missing robots.txt (allows all)

**Usage:**
```python
from src.scraping.robots_parser import RobotsChecker

checker = RobotsChecker(user_agent="MyBot/1.0")

# Check if URL can be fetched
if checker.can_fetch("https://example.com/page"):
    # Get recommended crawl delay
    delay = checker.get_crawl_delay("https://example.com/page")
    # Proceed with scraping
```

### 2. **Rate Limiting**

**Implementation:** `src/scraping/rate_limiter.py`

**Features:**
- Per-domain rate limiting
- Sliding window algorithm
- Concurrent request limiting
- robots.txt crawl delay integration
- Thread-safe implementation

**Configuration:**
```python
from src.scraping.rate_limiter import RateLimiter

limiter = RateLimiter(
    requests_per_second=1.0,      # Max requests per second per domain
    min_delay_seconds=2.0,         # Minimum delay between requests
    max_concurrent_requests=5,     # Max concurrent requests total
    respect_crawl_delay=True       # Honor robots.txt crawl delay
)
```

### 3. **Caching**

**Implementation:** `src/scraping/cache.py`

**Features:**
- File-based JSON caching
- Configurable TTL (time-to-live)
- Automatic expiration
- Cache statistics

**Benefits:**
- Reduces server load
- Speeds up development/testing
- Allows replay of requests
- Saves bandwidth

**Usage:**
```python
from src.scraping.cache import ScraperCache

cache = ScraperCache(
    cache_dir="data/cache",
    ttl_seconds=86400,  # 24 hours
    enabled=True
)

# Try to get from cache
content = cache.get(url)
if content is None:
    # Fetch and cache
    content = fetch_url(url)
    cache.set(url, content)
```

### 4. **Request Logging**

**Implementation:** `src/scraping/compliance.py`

**Features:**
- Logs all requests in JSONL format
- Includes timestamps, URLs, status
- Tracks blocks, errors, cache hits
- Enables auditing and debugging

**Log Format:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "url": "https://example.com/page",
  "status": "success",
  "user_agent": "MyBot/1.0 (+https://contact.com)",
  "cached": true
}
```

### 5. **Error Handling**

**Best Practices:**
- Respect HTTP status codes
- Handle 429 (Too Many Requests) with exponential backoff
- Handle 503 (Service Unavailable) gracefully
- Check Retry-After headers
- Log all errors for analysis

**Status Code Handling:**
- **200 OK:** Success, cache and process
- **404 Not Found:** Log and skip
- **429 Too Many Requests:** Wait and retry with backoff
- **503 Service Unavailable:** Respect Retry-After header
- **4xx Client Errors:** Log and investigate
- **5xx Server Errors:** Retry with exponential backoff (max 3 attempts)

### 6. **User-Agent Best Practices**

**Format:**
```
BotName/Version (+contact-url)
```

**Examples:**
- ✅ `OperaResearchBot/1.0 (+https://github.com/user/repo)`
- ✅ `ResearchBot/2.5 (+mailto:contact@example.com)`
- ❌ `Mozilla/5.0...` (Don't impersonate browsers)
- ❌ `Python-requests/2.28` (Too generic, no contact info)

**Why Contact Info Matters:**
- Website owners can reach you about concerns
- Demonstrates legitimacy and accountability
- May prevent IP bans
- Required by many website ToS

---

## Implementation Guide

### Using the Compliant Scraper

The recommended way to scrape is using `CompliantOperaScraper`:

```python
from src.scraping.compliant_scraper import CompliantOperaScraper

# Initialize with mandatory compliance parameters
scraper = CompliantOperaScraper(
    user_agent="OperaResearchBot/1.0",
    contact_info="https://github.com/austinkness/opera-research-agentic-system",
    respect_robots_txt=True,        # Always True for compliance
    enable_rate_limiting=True,      # Always True for compliance
    enable_caching=True,            # Recommended True
    requests_per_second=1.0,        # Conservative rate
    min_delay_seconds=2.0,          # Polite 2-second delay
    cache_ttl_seconds=86400         # 24-hour cache
)

# Scrape a URL
result = scraper.scrape_basic_info("https://www.example-opera.com")

if result['success']:
    print(f"Title: {result['title']}")
    print(f"Found {result['link_count']} links")
else:
    print(f"Failed: {result['error']}")

# Get compliance statistics
stats = scraper.get_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']}%")
print(f"URLs blocked by robots.txt: {stats['robots_blocked']}")
```

### Configuration Recommendations

**For Research/Academic Use:**
```python
scraper = CompliantOperaScraper(
    user_agent="ResearchBot/1.0",
    contact_info="mailto:researcher@university.edu",
    respect_robots_txt=True,
    enable_rate_limiting=True,
    enable_caching=True,
    requests_per_second=0.5,        # Very conservative
    min_delay_seconds=3.0,          # Extra polite
    cache_ttl_seconds=604800        # 7-day cache
)
```

**For Production Monitoring:**
```python
scraper = CompliantOperaScraper(
    user_agent="OperaMonitorBot/1.0",
    contact_info="https://your-company.com/bot-info",
    respect_robots_txt=True,
    enable_rate_limiting=True,
    enable_caching=True,
    requests_per_second=1.0,
    min_delay_seconds=2.0,
    cache_ttl_seconds=3600          # 1-hour cache for fresh data
)
```

### Manual Compliance Checks

Before scraping a new website:

1. **Check robots.txt manually:**
   ```
   https://example.com/robots.txt
   ```

2. **Review Terms of Service:**
   - Look for clauses about automated access
   - Check for API availability
   - Note any usage restrictions

3. **Test with small sample:**
   - Start with 5-10 pages
   - Monitor response times
   - Check for errors or blocks

4. **Document your assessment:**
   - Record legal review
   - Note any special permissions
   - Document rate limits

---

## Monitoring and Auditing

### Request Logs

All requests are logged to `data/scraping_log.jsonl`:

```bash
# View recent requests
tail -f data/scraping_log.jsonl

# Count requests by status
cat data/scraping_log.jsonl | jq '.status' | sort | uniq -c

# Find blocked requests
cat data/scraping_log.jsonl | jq 'select(.status == "blocked_by_robots")'

# Calculate success rate
cat data/scraping_log.jsonl | jq -s \
  'group_by(.status) | map({status: .[0].status, count: length})'
```

### Compliance Metrics

```python
# Get detailed statistics
stats = scraper.get_stats()

print(f"Total requests: {stats['total_requests']}")
print(f"Cache hit rate: {stats['cache_hit_rate']}%")
print(f"Robots.txt blocks: {stats['robots_blocked']}")
print(f"Errors: {stats['errors']}")
print(f"Cache size: {stats['cache_stats']['total_size_mb']} MB")
```

### Regular Audits

**Monthly Checklist:**
- [ ] Review request logs for errors
- [ ] Check for any robots.txt violations
- [ ] Verify rate limits are respected
- [ ] Clear expired cache entries
- [ ] Review any changes to target website ToS
- [ ] Update robots.txt cache if needed

**Commands:**
```python
# Clear expired cache
scraper.compliance.clear_expired_cache()

# Force refresh robots.txt
scraper.compliance.robots_checker.clear_cache()

# Get audit report
stats = scraper.get_stats()
```

---

## Troubleshooting

### Common Issues

#### 1. All Requests Blocked

**Symptoms:** `robots_blocked` count high

**Solutions:**
- Check robots.txt manually
- Verify your user-agent is correct
- Some sites block all bots - respect this
- Contact website owner for permission

#### 2. Slow Scraping

**Symptoms:** Taking too long to scrape

**Causes:**
- Rate limiting working as intended
- High crawl delay in robots.txt
- Conservative delay settings

**Solutions:**
- This is normal and ethical behavior
- Don't reduce delays below 1 second
- Use caching to avoid re-scraping
- Consider if you really need all the data

#### 3. HTTP 429 Errors

**Symptoms:** "Too Many Requests" errors

**Solutions:**
- Your rate limiting may be too aggressive
- Increase `min_delay_seconds`
- Decrease `requests_per_second`
- Check if site has published rate limits

#### 4. IP Banned

**Symptoms:** All requests fail with 403

**Solutions:**
- Stop scraping immediately
- Review compliance logs
- Contact website administrator
- Apologize and explain your purpose
- Wait for unban (typically 24-48 hours)
- Adjust scraping parameters

### Getting Help

If you're unsure about legal compliance:

1. **Consult a lawyer** - Especially for commercial use
2. **Contact website owner** - Ask for permission
3. **Use official APIs** - When available
4. **Join communities** - r/webscraping, Stack Overflow

---

## Country-Specific Regulations

### United States
- **CFAA:** Don't circumvent access controls
- **DMCA:** Don't bypass copyright protection
- **State Laws:** Check applicable state laws

### European Union
- **GDPR:** Strict personal data protection
- **Database Directive:** Sui generis database rights
- **E-Privacy Directive:** Cookie and tracking rules

### United Kingdom
- **Computer Misuse Act:** Criminal penalties for unauthorized access
- **DPA 2018:** Data protection requirements
- **Copyright Act:** Database rights

### Australia
- **Privacy Act:** Personal information protection
- **Copyright Act:** Database protection
- **Cybercrime Act:** Unauthorized access penalties

### Canada
- **PIPEDA:** Personal information protection
- **Copyright Act:** Database rights protection

---

## Additional Resources

### Documentation
- [robots.txt Specification](https://www.robotstxt.org/)
- [REP RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html)
- [GDPR Official Text](https://gdpr-info.eu/)

### Tools
- [robots.txt Tester](https://en.ryte.com/free-tools/robots-txt/)
- [User-Agent Checker](https://www.whatismybrowser.com/detect/what-is-my-user-agent)

### Legal Resources
- Consult with legal counsel for commercial projects
- Review EFF resources on CFAA
- Check local bar association for tech law specialists

---

## Conclusion

**Key Takeaways:**

1. ✅ **Always respect robots.txt**
2. ✅ **Include contact information in user-agent**
3. ✅ **Implement rate limiting (minimum 1-2s delays)**
4. ✅ **Use caching to reduce server load**
5. ✅ **Log all requests for auditing**
6. ✅ **Review Terms of Service**
7. ✅ **Protect personal data appropriately**
8. ✅ **Be transparent about your purpose**

**When in doubt:**
- Ask permission
- Consult legal counsel
- Use official APIs
- Err on the side of caution

This project implements all technical best practices. Legal compliance requires your judgment based on your jurisdiction and use case.

---

**Last Updated:** January 2025
**Version:** 1.0
**Maintainer:** Opera Research Agentic System Project
