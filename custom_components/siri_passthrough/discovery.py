"""Work out where the bridge is, so the user does not have to.

There is no way to look this up in the Home Assistant UI. The add-on runs with
host networking, so it has no address of its own and no port-mapping page --
the control API is simply on the *host's* interfaces, on the bridge's built-in
default port. Upstream's own integration defaults to 127.0.0.1, which is only
correct when Home Assistant Core runs on that same host OS; on Home Assistant OS
the add-on and Core are different containers and that address is wrong.

So rather than document a derivation, probe the handful of addresses the bridge
can plausibly be on and keep the first that answers.
"""

from __future__ import annotations

import asyncio
import logging
from urllib.parse import urlsplit

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

_PROBE_TIMEOUT = aiohttp.ClientTimeout(total=2)


def candidate_urls(hass: HomeAssistant) -> list[str]:
    """Addresses the bridge could be reachable on, best guess first."""
    hosts: list[str] = []

    # Whatever Home Assistant believes it is reachable as: on Home Assistant OS
    # this is the host the add-on is bound to.
    for url in (hass.config.internal_url, hass.config.external_url):
        if url:
            host = urlsplit(url).hostname
            if host:
                hosts.append(host)

    hosts.extend(
        [
            "homeassistant.local",
            # Core / Supervised, where the add-on shares the host with HA.
            "127.0.0.1",
            # The Supervisor network's host side, for host-networked add-ons.
            "172.30.32.1",
        ]
    )

    seen: set[str] = set()
    return [
        f"http://{h}:{DEFAULT_PORT}"
        for h in hosts
        if not (h in seen or seen.add(h))
    ]


async def probe(hass: HomeAssistant, url: str) -> bool:
    """True if something that looks like the bridge answers on this URL."""
    session = async_get_clientsession(hass)
    try:
        async with session.get(f"{url}/state", timeout=_PROBE_TIMEOUT) as resp:
            if resp.status >= 400:
                return False
            body = await resp.json(content_type=None)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        return False

    # /state always carries these, paired or not, which distinguishes the bridge
    # from whatever else might be sitting on the port.
    return isinstance(body, dict) and "targets" in body and "siriAvailable" in body


async def find_bridge(hass: HomeAssistant) -> str | None:
    """Return the first candidate URL that answers, or None."""
    for url in candidate_urls(hass):
        if await probe(hass, url):
            _LOGGER.debug("Found the bridge at %s", url)
            return url
    return None
