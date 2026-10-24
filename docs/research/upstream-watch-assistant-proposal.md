# Historical experiment proposal: native Wear OS assistant entry point for hold-to-talk

Superseded for contribution planning by `upstream-watch-assistant-spec.md` and `upstream-watch-assistant-cross-device.md`. Subsequent discovery found existing upstream issue #251 and PR #259 implementing this feature. Do not post this earlier draft as a duplicate issue; coordinate validation and focused follow-up on the existing work.

## User problem

On a Galaxy Watch7, the user wants holding the orange Home button to open Herald directly into its existing voice-input flow, as the default digital assistant rather than Google or Bixby. A double-press application shortcut is not equivalent.

## Proposed upstream direction

Discuss adding a native Android assistant entry point to Herald's Wear OS application, reusing its existing voice flow. The current exported watch activity already has a listening entry point, but the inspected application manifest does not advertise the Android ASSIST intent. This is a proposed design for maintainer discussion, not a claim that a manifest-only change is sufficient.

A separately signed bridge was used as a reversible feasibility experiment so the published phone/watch Herald signing relationship remained intact. An upstream implementation would not necessarily need that separate app, custom APK builder, or ADB setup tooling. Those are local experimental artifacts, not the proposed contribution's required architecture.

## Verified experiment

- Target device: Samsung Galaxy Watch7, Android 16 / API36.
- Separate exported assistant activity installed and accepted as the Android assistant role holder without bypassing qualification.
- Samsung Home-hold assistant mode selected and policy read back as LONG_PRESS_POWER_ASSISTANT.
- Firmware inspection found that this mode calls generic assistant dispatch rather than an explicit Google component. Firmware-specific behavior should not be generalized to all Wear OS devices.
- Real on-device instrumentation verified the bridge's outgoing explicit Herald intent and listening boolean while blocking actual Herald launches before microphone activation.
- Seventeen host regression tests passed, and original assistant/button state was restored and verified before reapplying the candidate.
- No official Herald APK was re-signed; no phone or Gateway changes were made.

## Current unresolved user-observed behavior

After the configuration, the user reports that a physical Home-button hold shows "Complete action using" with "Speech recognition" and "Samsung Keyboard" choices. We have NOT established which exact intent/component produced that chooser, nor which selection gives the intended behavior. We do not treat this report as successful voice or agent-reply acceptance. A later screenshot attempt returned a black display, so it did not validate the chooser's contents or origin.

## Suggested acceptance criteria

- A user can select Herald through the device's supported default-assistant UI where available.
- A configured physical Home-button hold enters the intended Herald voice flow without an unexpected chooser.
- Cold, warm and repeated invocation behave correctly; activity recreation does not activate voice again without a new invocation.
- Microphone permission, speech input versus live voice, unavailable phone/Gateway, cancellation and return navigation behave explicitly and safely.
- Existing Chat identity and phone/watch signing compatibility are preserved.
- No always-on listening, broad accessibility privileges or app impersonation is required.
- Document device-specific button setup, limitations and how to restore the previous assistant.

## Contribution status and maintainer question

The experiment and outstanding checks are tracked in the contributor's fork at https://github.com/teknightstick/herald/pull/5 (draft). It is not an upstream PR and is not ready to merge as a finished feature. The fork contains research and local tooling that should be separated from a focused upstream change.

Would the maintainers welcome a native Wear OS assistant entry point, and what architecture and device coverage would they prefer? We would follow the repository's issue-first contribution guidance, agree the approach, then prepare a focused PR with regression tests and actual device acceptance evidence.
