# Changelog

## v0.4.0

- Guided setup. The flow now finds the bridge, waits for an Apple TV to be
  paired with it (explaining the `-6718` pairing trap if it is hit), and offers
  to build the assist pipeline wired to the right pair of entities.
- Repairs entries when the chain breaks: bridge unreachable, nothing paired, or
  no pipeline using the provider. Checked every 15 minutes, cleared when fixed.
  Previously all three failed silently — the microphone just did nothing.

## v0.3.1

- Show something on screen: the placeholder transcript is now "Asked Siri"
  rather than a marker string, so a satellite that displays recognised text has
  a readable status line instead of nothing.


## v0.3.0

- Route per utterance, so one pipeline can serve both the television and the
  house. Set an entity and the states it should be in; while that holds the
  audio goes to Siri, otherwise it is handed to a normal speech-to-text engine
  and answered by a normal conversation agent.
- The conversation agent delegates a real transcript instead of always staying
  silent, so it cannot talk over Siri's reply.
- Routing is editable after setup through an options flow.

## v0.2.0

- Find the bridge automatically instead of asking you to derive its URL.
- Validate a submitted URL by checking the response is actually bridge-shaped.

## v0.1.0

- Initial release: a speech-to-text provider that streams the pipeline's live
  audio to Siri instead of transcribing it, plus a silent conversation agent so
  the sentinel transcript does not produce "sorry, I didn't understand".
