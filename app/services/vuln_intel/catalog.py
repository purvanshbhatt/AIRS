"""
Product knowledge used to route a piece of software to the right public
intelligence source.

Only products listed here are looked up by CPE in NVD; library packages are
looked up in OSV by ecosystem; everything else is reported with status
``unknown`` rather than guessed at. Windows and Office have no CVE mapping
here on purpose (Microsoft ships fixes as cumulative updates, not versions
you can compare), so they only get end-of-life information.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

CATEGORIES = (
    "os", "runtime", "database", "web_server", "framework",
    "application", "cloud_service", "library",
)


@dataclass(frozen=True)
class ProductInfo:
    key: str                                  # canonical dedupe key
    name: str                                 # display name
    vendor: Optional[str] = None
    category: str = "application"
    cpe: Optional[Tuple[str, str]] = None     # (vendor, product) in NVD CPE terms
    osv: Optional[Tuple[str, str]] = None     # (ecosystem, package name)
    eol: Optional[str] = None                 # endoflife.date product slug
    apt: Optional[str] = None                 # package name for apt
    rpm: Optional[str] = None                 # package name for dnf / yum
    known: bool = True


def _p(key, name, vendor, category, cpe=None, osv=None, eol=None, apt=None, rpm=None) -> ProductInfo:
    return ProductInfo(key=key, name=name, vendor=vendor, category=category,
                       cpe=cpe, osv=osv, eol=eol, apt=apt, rpm=rpm)


# canonical key -> ProductInfo
PRODUCTS: Dict[str, ProductInfo] = {p.key: p for p in [
    # --- well-known products matched in NVD by CPE -----------------------
    _p("php", "PHP", "The PHP Group", "runtime", ("php", "php"), eol="php", apt="php", rpm="php"),
    _p("nginx", "nginx", "F5, Inc.", "web_server", ("f5", "nginx"), eol="nginx", apt="nginx", rpm="nginx"),
    _p("apache-http-server", "Apache HTTP Server", "Apache Software Foundation", "web_server",
       ("apache", "http_server"), eol="apache-http-server", apt="apache2", rpm="httpd"),
    _p("openssl", "OpenSSL", "OpenSSL Project", "library", ("openssl", "openssl"), eol="openssl",
       apt="openssl", rpm="openssl"),
    _p("openssh", "OpenSSH", "OpenBSD Project", "application", ("openbsd", "openssh"),
       apt="openssh-server", rpm="openssh-server"),
    _p("postgresql", "PostgreSQL", "PostgreSQL Global Development Group", "database",
       ("postgresql", "postgresql"), eol="postgresql", apt="postgresql", rpm="postgresql"),
    _p("mysql", "MySQL", "Oracle Corporation", "database", ("oracle", "mysql"), eol="mysql",
       apt="mysql-server", rpm="mysql-server"),
    _p("mariadb", "MariaDB", "MariaDB Foundation", "database", ("mariadb", "mariadb"), eol="mariadb",
       apt="mariadb-server", rpm="mariadb-server"),
    _p("nodejs", "Node.js", "OpenJS Foundation", "runtime", ("nodejs", "node.js"), eol="nodejs",
       apt="nodejs", rpm="nodejs"),
    _p("python", "Python", "Python Software Foundation", "runtime", ("python", "python"), eol="python",
       apt="python3", rpm="python3"),
    _p("wordpress", "WordPress", "WordPress Foundation", "application", ("wordpress", "wordpress"),
       eol="wordpress"),
    _p("drupal", "Drupal", "Drupal Association", "application", ("drupal", "drupal"), eol="drupal"),
    _p("tomcat", "Apache Tomcat", "Apache Software Foundation", "web_server", ("apache", "tomcat"),
       eol="tomcat", apt="tomcat9", rpm="tomcat"),
    _p("redis", "Redis", "Redis Ltd.", "database", ("redis", "redis"), eol="redis",
       apt="redis-server", rpm="redis"),
    _p("mongodb", "MongoDB", "MongoDB Inc.", "database", ("mongodb", "mongodb"), eol="mongodb",
       apt="mongodb-org", rpm="mongodb-org"),
    _p("elasticsearch", "Elasticsearch", "Elastic NV", "database", ("elastic", "elasticsearch"),
       eol="elasticsearch", apt="elasticsearch", rpm="elasticsearch"),
    _p("kubernetes", "Kubernetes", "Cloud Native Computing Foundation", "runtime",
       ("kubernetes", "kubernetes"), eol="kubernetes"),
    _p("golang", "Go", "Google LLC", "runtime", ("golang", "go"), eol="go"),
    # --- desktop software reported by Intune / Defender / Wazuh ------------
    # Browsers ship a new major release every few weeks and NVD lists thousands of CVEs
    # per old build, so they are judged by release-cycle end of life, not by CPE matching.
    _p("chrome", "Google Chrome", "Google LLC", "application", eol="chrome"),
    _p("firefox", "Mozilla Firefox", "Mozilla", "application", eol="firefox"),
    _p("edge", "Microsoft Edge", "Microsoft Corporation", "application"),
    _p("7-zip", "7-Zip", "Igor Pavlov", "application", ("7-zip", "7-zip")),
    _p("vlc", "VLC media player", "VideoLAN", "application", ("videolan", "vlc_media_player")),
    _p("putty", "PuTTY", "Simon Tatham", "application", ("putty", "putty")),
    _p("winrar", "WinRAR", "RARLAB", "application", ("rarlab", "winrar")),
    _p("teamviewer", "TeamViewer", "TeamViewer", "application", ("teamviewer", "teamviewer")),
    _p("acrobat-reader", "Adobe Acrobat Reader", "Adobe Inc.", "application", ("adobe", "acrobat_reader_dc")),
    # Recognised, but no version-comparable public feed: reported as "not checked".
    _p("zoom", "Zoom", "Zoom Video Communications", "application"),
    _p("microsoft-teams", "Microsoft Teams", "Microsoft Corporation", "application"),
    _p("microsoft-onedrive", "Microsoft OneDrive", "Microsoft Corporation", "application"),
    # --- end-of-life information only (no CVE mapping) -------------------
    _p("docker", "Docker Engine", "Docker, Inc.", "runtime", eol="docker-engine"),
    _p("java", "Java", "Oracle Corporation", "runtime"),
    _p("microsoft-office", "Microsoft Office", "Microsoft Corporation", "application"),
    _p("microsoft-365-apps", "Microsoft 365 Apps", "Microsoft Corporation", "application"),
    # --- libraries / frameworks matched in OSV by ecosystem ---------------
    _p("django", "Django", "Django Software Foundation", "framework", osv=("PyPI", "django"), eol="django"),
    _p("flask", "Flask", "Pallets", "framework", osv=("PyPI", "flask")),
    _p("fastapi", "FastAPI", None, "framework", osv=("PyPI", "fastapi")),
    _p("requests", "Requests", None, "library", osv=("PyPI", "requests")),
    _p("jinja2", "Jinja2", "Pallets", "library", osv=("PyPI", "jinja2")),
    _p("pillow", "Pillow", None, "library", osv=("PyPI", "pillow")),
    _p("urllib3", "urllib3", None, "library", osv=("PyPI", "urllib3")),
    _p("react", "React", "Meta", "framework", osv=("npm", "react"), eol="react"),
    _p("express", "Express", "OpenJS Foundation", "framework", osv=("npm", "express")),
    _p("angular", "Angular", "Google LLC", "framework", osv=("npm", "@angular/core"), eol="angular"),
    _p("vue", "Vue.js", None, "framework", osv=("npm", "vue"), eol="vue"),
    _p("nextjs", "Next.js", "Vercel", "framework", osv=("npm", "next"), eol="nextjs"),
    _p("lodash", "Lodash", None, "library", osv=("npm", "lodash")),
    _p("jquery", "jQuery", "OpenJS Foundation", "library", osv=("npm", "jquery"), eol="jquery"),
    _p("axios", "Axios", None, "library", osv=("npm", "axios")),
    _p("laravel", "Laravel", "Laravel LLC", "framework", osv=("Packagist", "laravel/framework"), eol="laravel"),
    _p("symfony", "Symfony", "Symfony SAS", "framework", osv=("Packagist", "symfony/symfony"), eol="symfony"),
    _p("spring-boot", "Spring Boot", "VMware", "framework",
       osv=("Maven", "org.springframework.boot:spring-boot"), eol="spring-boot"),
    _p("spring-framework", "Spring Framework", "VMware", "framework",
       osv=("Maven", "org.springframework:spring-core"), eol="spring-framework"),
    _p("log4j", "Apache Log4j", "Apache Software Foundation", "library",
       osv=("Maven", "org.apache.logging.log4j:log4j-core"), eol="log4j"),
    _p("rails", "Ruby on Rails", None, "framework", osv=("RubyGems", "rails"), eol="rails"),
]}

# alias (lower-case) -> canonical key
ALIASES: Dict[str, str] = {
    "php-cli": "php", "php-fpm": "php", "php-common": "php", "libapache2-mod-php": "php",
    "nginx-core": "nginx", "nginx-full": "nginx", "nginx-light": "nginx",
    "apache": "apache-http-server", "apache2": "apache-http-server", "httpd": "apache-http-server",
    "apache httpd": "apache-http-server", "apache-httpd": "apache-http-server",
    "apache http server": "apache-http-server", "apache2-bin": "apache-http-server",
    "openssl-libs": "openssl",
    "openssh-server": "openssh", "openssh-client": "openssh", "openssh-clients": "openssh",
    "postgres": "postgresql", "postgresql-server": "postgresql", "postgresql-client": "postgresql",
    "aurora-postgresql": "postgresql",
    "mysql-server": "mysql", "mysql-community-server": "mysql", "mysql community server": "mysql",
    "mariadb-server": "mariadb",
    "node": "nodejs", "node.js": "nodejs", "node js": "nodejs",
    "python3": "python", "cpython": "python", "py": "python",
    "apache tomcat": "tomcat", "tomcat9": "tomcat", "tomcat10": "tomcat",
    "redis-server": "redis",
    "mongod": "mongodb", "mongodb-org": "mongodb", "mongodb-org-server": "mongodb", "mongodb server": "mongodb",
    "k8s": "kubernetes", "kubelet": "kubernetes",
    "go": "golang",
    "docker-ce": "docker", "docker engine": "docker", "docker-engine": "docker",
    "openjdk": "java", "jdk": "java", "jre": "java",
    # Intune / Defender / Wazuh display names (after canonicalisation, see normalize_display_name)
    "google chrome": "chrome", "google-chrome-stable": "chrome", "google-chrome": "chrome",
    "mozilla firefox": "firefox",
    "microsoft edge": "edge", "microsoft-edge-stable": "edge",
    "7zip": "7-zip", "p7zip": "7-zip",
    "vlc media player": "vlc",
    "putty release": "putty",
    "adobe acrobat reader": "acrobat-reader", "adobe acrobat reader dc": "acrobat-reader",
    "adobe reader": "acrobat-reader",
    "zoom workplace": "zoom", "zoom meetings": "zoom",
    "teams": "microsoft-teams", "microsoft teams classic": "microsoft-teams",
    "onedrive": "microsoft-onedrive",
    "postgresql 15": "postgresql",
    "office": "microsoft-office", "microsoft office": "microsoft-office",
    "microsoft 365": "microsoft-365-apps", "microsoft 365 apps": "microsoft-365-apps",
    "microsoft 365 apps for enterprise": "microsoft-365-apps",
    "microsoft 365 apps for business": "microsoft-365-apps",
    "next": "nextjs", "next.js": "nextjs", "vue.js": "vue", "angularjs": "angular",
    "spring boot": "spring-boot", "spring-core": "spring-framework", "spring": "spring-framework",
    "log4j-core": "log4j", "apache log4j": "log4j", "log4j2": "log4j",
    "ruby on rails": "rails", "laravel/framework": "laravel",
}

# "<ecosystem>:<package>" prefixes a user may type for a manual entry.
ECOSYSTEM_PREFIXES: Dict[str, str] = {
    "pypi": "PyPI", "pip": "PyPI", "npm": "npm", "packagist": "Packagist", "composer": "Packagist",
    "maven": "Maven", "go": "Go", "golang": "Go", "gem": "RubyGems", "rubygems": "RubyGems",
    "nuget": "NuGet", "cargo": "crates.io", "crates.io": "crates.io",
}

# installation_source substrings that name a language package manager.
_SOURCE_ECOSYSTEMS: List[Tuple[str, str]] = [
    ("pypi", "PyPI"), ("pip", "PyPI"), ("npm", "npm"), ("composer", "Packagist"),
    ("packagist", "Packagist"), ("maven", "Maven"), ("rubygems", "RubyGems"), ("nuget", "NuGet"),
]

# Linux package-name suffixes that still name the same product (exact suffix only).
_SUFFIXES = ("-server", "-client", "-common", "-cli", "-fpm", "-libs", "-core", "-bin", "-community")
_TRAILING_VERSION = re.compile(r"[\s\-_]*v?\d+(?:\.\d+)*$")
_PAREN = re.compile(r"\s*\([^)]*\)\s*")
_LOCALE_SUFFIX = re.compile(r"\s+-\s+[a-z]{2}-[a-z]{2}$")

LEGACY_CATEGORY_MAP = {
    "language runtime": "runtime", "runtime": "runtime", "language": "runtime",
    "framework": "framework", "database": "database", "web server": "web_server", "server": "web_server",
    "operating system": "os", "operating_system": "os", "os": "os", "library": "library",
    "container runtime": "runtime", "ci/cd": "application", "other": "application",
    "application": "application", "cloud service": "cloud_service", "cloud_service": "cloud_service",
}


def _lookup(token: str) -> Optional[ProductInfo]:
    token = token.strip().lower()
    if not token:
        return None
    key = ALIASES.get(token, token)
    return PRODUCTS.get(key)


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name or "").strip().lower())


def normalize_display_name(name: str) -> List[str]:
    """Canonical spellings of a display name, most specific first.

    Fixed, documented steps only (no similarity scoring, no substring search):
      1. lower-case, collapse whitespace           "Google Chrome"            -> "google chrome"
      2. drop parenthetical notes                  "Python 3.11.4 (64-bit)"   -> "python 3.11.4"
      3. drop a trailing locale                    "... - en-us"              -> "..."
      4. drop a trailing version number            "python 3.11.4", "php8.1"  -> "python", "php"
      5. drop one exact Linux package suffix       "postgresql15-server"      -> "postgresql15" -> "postgresql"
    """
    raw = normalize_name(name)
    out: List[str] = [raw]
    no_paren = normalize_name(_PAREN.sub(" ", raw))
    out.append(no_paren)
    no_locale = _LOCALE_SUFFIX.sub("", no_paren).strip()
    out.append(no_locale)
    stripped = _TRAILING_VERSION.sub("", no_locale).strip()
    out.append(stripped)
    for suffix in _SUFFIXES:
        if stripped.endswith(suffix):
            base = stripped[: -len(suffix)]
            out.append(base)
            out.append(_TRAILING_VERSION.sub("", base).strip())
    seen: List[str] = []
    for cand in out:
        if cand and cand not in seen:
            seen.append(cand)
    return seen


def canonical_slug(name: str) -> Optional[str]:
    """Canonical product slug for a display name, or None when it is not in the alias table."""
    for cand in normalize_display_name(name):
        info = _lookup(cand)
        if info:
            return info.key
    return None


def resolve_product(
    name: str,
    vendor: Optional[str] = None,
    source: Optional[str] = None,
    legacy_category: Optional[str] = None,
) -> ProductInfo:
    """Map a raw product name to what we know about it.

    Matching is an explicit alias table over canonicalised names. It never
    guesses by substring or similarity: ``python3-requests`` is not Python and
    "Mozilla Firefox ESR" is not Firefox. Names that are not in the table come
    back with ``known=False`` and stay in the inventory as "not checked".
    """
    raw = normalize_name(name)

    # Explicit "<ecosystem>:<package>" (manual entries, SBOM-style sources).
    if ":" in raw:
        prefix, rest = raw.split(":", 1)
        eco = ECOSYSTEM_PREFIXES.get(prefix.strip())
        if eco and rest.strip():
            package = rest.strip()
            return ProductInfo(
                key=f"{eco.lower()}:{package}", name=package, vendor=vendor, category="library",
                osv=(eco, package),
            )

    slug = canonical_slug(name)
    if slug:
        return PRODUCTS[slug]

    # A language package manager named as the source -> OSV by ecosystem.
    src = (source or "").lower()
    for needle, eco in _SOURCE_ECOSYSTEMS:
        if needle in src:
            return ProductInfo(
                key=f"{eco.lower()}:{raw}", name=str(name).strip(), vendor=vendor,
                category="library", osv=(eco, raw),
            )

    category = LEGACY_CATEGORY_MAP.get((legacy_category or "").strip().lower(), "application")
    return ProductInfo(
        key=raw, name=str(name).strip() or raw, vendor=vendor, category=category, known=False,
    )


# ---------------------------------------------------------------------------
# Operating systems
# ---------------------------------------------------------------------------

@dataclass
class OSInfo:
    name: str
    version: Optional[str]
    family: str                               # windows | ubuntu | debian | alpine | amazon | rhel | macos
    eol: Optional[str] = None                 # endoflife.date slug
    cycles: List[str] = field(default_factory=list)   # candidate endoflife cycles, best first
    osv_ecosystem: Optional[str] = None       # e.g. "Ubuntu:22.04:LTS", "Debian:12", "Alpine:v3.19"
    package_manager: Optional[str] = None     # apt | dnf | yum | apk | windows_update | macos_update

    @property
    def key(self) -> str:
        return self.name.lower().replace(" ", "-")


_WINDOWS_BUILDS = {
    "19041": ("10", "2004"), "19042": ("10", "20H2"), "19043": ("10", "21H1"),
    "19044": ("10", "21H2"), "19045": ("10", "22H2"),
    "22000": ("11", "21H2"), "22621": ("11", "22H2"), "22631": ("11", "23H2"),
    "26100": ("11", "24H2"), "26200": ("11", "25H2"),
}
_GENERIC_OS = {"", "linux", "linux/unix", "unix", "unknown", "other", "windows"}


def parse_os(os_string: Optional[str], version: Optional[str] = None) -> Optional[OSInfo]:
    """Parse an operating-system string from EC2, SSM, Intune or Wazuh.

    Returns None for strings that carry no usable identity ("Linux/UNIX").
    """
    text = " ".join(str(x) for x in (os_string, version) if x).strip()
    low = text.lower()
    if not low or (low in _GENERIC_OS and not version):
        return None

    if "windows" in low:
        if "server" in low:
            m = re.search(r"\b(2008|2012|2016|2019|2022|2025)(\s*r2)?\b", low)
            if not m:
                return OSInfo("Windows Server", None, "windows", eol="windows-server",
                              package_manager="windows_update")
            year = m.group(1)
            cycle = f"{year}-r2" if m.group(2) else year
            return OSInfo("Windows Server", f"{year} R2" if m.group(2) else year, "windows",
                          eol="windows-server", cycles=[cycle], package_manager="windows_update")
        major: Optional[str] = None
        release: Optional[str] = None
        build = re.search(r"\b10\.0\.(\d{5})\b", low)
        if build and build.group(1) in _WINDOWS_BUILDS:
            major, release = _WINDOWS_BUILDS[build.group(1)]
        else:
            m = re.search(r"windows\s+(10|11)\b", low)
            if m:
                major = m.group(1)
            r = re.search(r"\b(\d{2}h[12]|1[5-9]0[3-9]|1[5-9]1[01]|2004)\b", low)
            if r:
                release = r.group(1).upper()
        if not major:
            return OSInfo("Windows", None, "windows", eol="windows", package_manager="windows_update")
        cycles: List[str] = []
        if release:
            rel = release.lower()
            enterprise = "enterprise" in low or "education" in low
            suffixes = ["-e", "-w"] if enterprise else ["-w", "-e"]
            cycles = [f"{major}-{rel}"] + [f"{major}-{rel}{s}" for s in suffixes]
        return OSInfo(f"Windows {major}", release, "windows", eol="windows", cycles=cycles,
                      package_manager="windows_update")

    if "amazon linux" in low or low.startswith("amzn"):
        m = re.search(r"amazon linux\s*(?:release\s*)?(2023|2)\b", low)
        ver = m.group(1) if m else None
        return OSInfo("Amazon Linux", ver, "amazon", eol="amazon-linux", cycles=[ver] if ver else [],
                      package_manager="dnf" if ver == "2023" else "yum")

    if "ubuntu" in low:
        m = re.search(r"(\d{2}\.\d{2})(?:\.\d+)?", low)
        full = re.search(r"\d{2}\.\d{2}(?:\.\d+)?", low)
        if not m:
            return OSInfo("Ubuntu", None, "ubuntu", eol="ubuntu", package_manager="apt")
        rel = m.group(1)
        year, month = rel.split(".")
        lts = int(year) % 2 == 0 and month == "04"
        return OSInfo("Ubuntu", full.group(0) if full else rel, "ubuntu", eol="ubuntu", cycles=[rel],
                      osv_ecosystem=f"Ubuntu:{rel}:LTS" if lts else f"Ubuntu:{rel}", package_manager="apt")

    if "debian" in low:
        m = re.search(r"\b(\d{1,2})(?:\.\d+)?\b", low)
        if not m:
            return OSInfo("Debian", None, "debian", eol="debian", package_manager="apt")
        return OSInfo("Debian", m.group(0), "debian", eol="debian", cycles=[m.group(1)],
                      osv_ecosystem=f"Debian:{m.group(1)}", package_manager="apt")

    if "alpine" in low:
        m = re.search(r"v?(\d+\.\d+)(?:\.\d+)?", low)
        if not m:
            return OSInfo("Alpine Linux", None, "alpine", eol="alpine-linux", package_manager="apk")
        return OSInfo("Alpine Linux", m.group(0).lstrip("v"), "alpine", eol="alpine-linux", cycles=[m.group(1)],
                      osv_ecosystem=f"Alpine:v{m.group(1)}", package_manager="apk")

    for needle, name, slug in (
        ("red hat", "Red Hat Enterprise Linux", "rhel"), ("rhel", "Red Hat Enterprise Linux", "rhel"),
        ("centos", "CentOS", "centos"), ("rocky", "Rocky Linux", "rocky-linux"),
        ("almalinux", "AlmaLinux", "almalinux"), ("fedora", "Fedora", "fedora"),
        ("oracle linux", "Oracle Linux", "oracle-linux"), ("suse", "SUSE Linux Enterprise", "sles"),
    ):
        if needle in low:
            m = re.search(r"\b(\d{1,2})(?:\.\d+)*\b", low)
            return OSInfo(name, m.group(0) if m else None, "rhel", eol=slug,
                          cycles=[m.group(1)] if m else [], package_manager="dnf")

    if "macos" in low or "mac os" in low or "os x" in low:
        m = re.search(r"\b(\d{2})(?:\.\d+)*\b", low)
        return OSInfo("macOS", m.group(0) if m else None, "macos", eol="macos",
                      cycles=[m.group(1)] if m else [], package_manager="macos_update")

    return None
