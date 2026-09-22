"""Work out where the bridge is, so the user does not have to.

The add-on binds its control API to 127.0.0.1, and Home Assistant Core reaches
it there: on Home Assistant OS, Supervised and the usual Docker install, Core
runs with host networking and shares the host's loopback with the add-on. So
loopback is tried first. The others exist for a bridge that runs somewhere
else -- a standalone container on another machine, say -- and are only reached
if loopback does not answer.

A note on the order, learned the hard way: with the bridge briefly bound to
every interface, any candidate answers, and whichever comes first is what gets
saved. An earlier version of this list put ``homeassistant.local`` ahead of
loopback; the saved URL then resolved (from inside Core) to the Supervisor
gateway, and the moment the bridge went back to loopback-only, Siri stopped.
Loopback first makes the saved URL the one that keeps working.
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
    hosts: list[str] = [
        # Where the add-on listens, and where Core reaches it on every same-host
        # install. Always first -- see the module docstring for why.
        "127.0.0.1",
        # The Supervisor network's host side, for a Core that is somehow not
        # host-networked.
        "172.30.32.1",
        "homeassistant.local",
    ]

    # Whatever Home Assistant believes it is reachable as, for a bridge that
    # runs on a different machine and was pointed at from there.
    for url in (hass.config.internal_url, hass.config.external_url):
        if url:
            host = urlsplit(url).hostname
            if host:
                hosts.append(host)

    seen: set[str] = set()
    return [
        f"http://{h}:{DEFAULT_PORT}"
        for h in hosts
        if not (h in seen or seen.add(h))
    ]


async def read_state(hass: HomeAssistant, url: str) -> dict | None:
    """The bridge's /state, or None if it cannot be read."""
    session = async_get_clientsession(hass)
    try:
        async with session.get(f"{url}/state", timeout=_PROBE_TIMEOUT) as resp:
            if resp.status >= 400:
                return None
            body = await resp.json(content_type=None)
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError):
        return None
    return body if isinstance(body, dict) else None


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
