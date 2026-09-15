# Changelog

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
