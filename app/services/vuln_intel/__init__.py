"""
Vulnerability intelligence for the organization's technology stack.

Pipeline (all deterministic, no LLM):

    inventory.collect_inventory()   what software/versions the org runs
        -> service.VulnIntelService  looks each product up online (cached 24 h)
              clients.OSVClient      https://api.osv.dev        (library / distro packages)
              clients.NVDClient      https://services.nvd.nist.gov (well-known products, CPE)
              clients.KEVClient      CISA Known Exploited Vulnerabilities catalog
              clients.EOLClient      https://endoflife.date     (support status, latest version)
        -> matcher                   keeps only CVEs whose affected range contains the installed version
        -> remediation               plain-language fix steps

``web_scanner`` passively checks the organization's public websites and
``cloud_deployments`` lists what is deployed in the connected AWS account.

Nothing here ever invents a vulnerability: when a source cannot be reached
the cached answer is used and the failure is reported in ``sources``.
"""

from app.services.vuln_intel.service import VulnIntelService, IntelClients  # noqa: F401
