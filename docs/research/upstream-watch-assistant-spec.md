# Spec draft: cross-watch setup and validation for Herald's native Wear OS assistant

## Problem Statement

A Wear OS user should be able to choose Herald as the watch's digital assistant and deliberately invoke its voice flow using the gesture their watch actually supports. Users need a trustworthy explanation of what is enabled, how to set it up, how to undo it, and what to do if their watch cannot route that gesture to Herald. Installing the app, choosing the assistant, configuring a manufacturer's button and choosing a speech-input handler are different operations; the UI must not confuse them.

This is a contribution to the existing upstream issue [#251](https://github.com/Giton22/herald/issues/251) and review/validation of its linked [PR #259](https://github.com/Giton22/herald/pull/259), not a replacement proposal or duplicate implementation. PR #259 was inspected at revision `cd3223c527f7d8153efc202b4f29d9b09128a098`. Its author reports OnePlus Watch 2 testing; we have not independently repeated those results. Our Galaxy Watch7 experiment used a separate bridge plus official Herald 0.13.0, not that PR. Our chooser observation must not be attributed to the PR without reproducing it on that code.

## Solution

### Native feature, optional through the operating system

Reuse the native assistant entry, session and setup row proposed in PR #259. Do not upstream the separate bridge APK, private device settings, custom build toolchain or Samsung ADB script as prerequisites for ordinary users.

For the first version, recommend **no independent master on/off switch**. This matches the PR's current direction: the operating system owns the assistant selection. Herald being available in the assistant list does not mean it has been selected or that it may listen continuously.

The user-facing assistant area should distinguish these states:

- **Not selected:** offer "Choose assistant" and explain that the system will ask the user to select Herald. Do not select it silently.
- **Selected:** report "Herald is your default assistant"; offer "Change assistant" and separate button-setup guidance. Do not say "Herald answers the button" solely because the role is held: the Samsung experiment showed a separately configured Bixby button mode.
- **Unavailable on this watch:** explain that the supported assistant selection path is not available; do not show a working-looking dead button or claim unsupported hardware. Preserve normal Herald, tile and complication access.
- **Setup canceled or selection changed elsewhere:** refresh actual system state when the watch app resumes. A remembered local flag is not authoritative.

Turning assistant integration off means opening the same system assistant screen and selecting the previous assistant or the system's None option **if that device offers one**. Herald cannot promise an arbitrary role change/clear on every OEM build. If the user also changed an OEM button mapping, explain that this may need to be restored separately. Never silently change it on the user's behalf.

A separate "Listen automatically" preference, if maintainers want one, would be a different feature: whether a deliberate invocation starts capture immediately or shows a tap-to-talk panel. It must not pretend to change the default assistant. Do not add that extra preference in this proposal without maintainer agreement; #251 currently requests immediate listening on deliberate invocation.

### First-time user journey

1. Install a released Herald phone/watch pair using the normal distribution/update path. Keep application identity and signing compatible so the watch's existing phone relay works.
2. Open Herald on the watch and establish the existing phone/Gateway connection. Assistant setup does not create an account, Gateway, Profile, Bot Chat or new set of credentials.
3. Open Herald's Assistant settings. Explain that this replaces the watch's default assistant only if selected in system settings, that it does not provide a wake word, and that it does not make Herald a standalone watch client.
4. Open a supported system assistant-selection screen. Prefer an actually resolvable Wear OS settings route. Do not assume the generic Android role-request dialog is requestable; handle absent screens, rejected requests and cancelation without crashing or reporting success.
5. User selects Herald. On return/resume, query actual role state rather than treating a successful settings launch as selection.
6. Show manufacturer-appropriate guidance for the relevant button/gesture, separately from role ownership. Where the OEM supports selecting a launch activity instead of role invocation, document the native dedicated voice-launch entry from PR #259. Do not write undocumented settings or promise a button remap from an ordinary app.
7. Offer an explicit "Try assistant" step. Before recording, make it clear that the microphone will open; obtain the normal audio permission if needed. Test the actual configured hardware gesture and show whether input reached Herald, not just whether the app holds a role.
8. A completed test includes a deliberate spoken Prompt and a real Reply via the existing phone/Gateway route. An empty-audio response proves some relay behavior but not intelligible speech recognition or a useful voice conversation.

### Watch compatibility strategy

Use platform capabilities first and manufacturer guidance second. Do not implement a blanket list of supported watches based only on a model name or a successful assistant-role assignment.

- **Samsung Galaxy Watch running Wear OS:** validate default-assistant selection separately from Samsung's Home-button press-and-hold choice. The investigated Watch7 firmware has a generic assistant mode distinct from Bixby mode. This is firmware-specific evidence, not a guarantee for every Galaxy model/software version. Do not install the separate bridge for the native feature.
- **OnePlus Watch running Wear OS:** PR #259 reports both native assistant-session and explicit voice-launch activity paths on a OnePlus Watch 2. Preserve that work and request the author's review of any change that would affect it. Exact button instructions require tested model/OS details, not a generic "hold Home" instruction.
- **Google Pixel Watch:** research and validate the actual assistant-selection and side-button behavior. Official instructions describing Google's assistant gesture do not establish third-party replacement support. Until native Herald is tested, mark this combination unverified.
- **Other Wear OS watches:** expose setup only where the role/settings route is usable, then require device evidence before documenting a hardware mapping. Unsupported button routing must not break the rest of Herald.
- **Older Samsung Tizen watches, Apple Watch and other non-Wear OS systems:** outside the Android wearApp feature. Do not suggest this APK or setup will work there.

Maintain a small evidence matrix with manufacturer/model, watch software/API, Herald revision/build variant, phone/watch signing compatibility, selector availability, role invocation, hardware gesture, capture path, real speech/Reply and disable/rollback results. Use "verified", "author-reported", "unverified" and "unsupported by this implementation" honestly. Do not promote a family to verified from one model.

## User Stories

1. As a Wear OS user, I want to know whether Herald can be my assistant on my watch, so that I do not follow instructions for an unsupported device.
2. As a user, I want installing or updating Herald to leave my current assistant selected, so that a new capability does not take over my watch.
3. As a user, I want a system-confirmed opt-in flow, so that I knowingly choose Herald instead of another assistant.
4. As a user, I want the setup row to reflect the current system selection, so that changing assistants elsewhere is not misreported.
5. As a user, I want canceled or unavailable setup handled clearly, so that I do not mistake an opened settings screen for successful setup.
6. As a Samsung user, I want assistant selection and Home-hold mapping explained separately, so that a Bixby button mode is not mistaken for a failed assistant role.
7. As a OnePlus user, I want an explicitly voice-starting launch target when my OEM maps a button to an activity, so that plain app launch does not require another tap.
8. As a Pixel Watch user, I want tested instructions or a clear unverified status, so that Google's documented gesture is not falsely advertised as third-party support.
9. As a user of another Wear OS watch, I want capability-based setup and accurate limitations, so that the app does not assume Samsung-specific controls.
10. As a user, I want an explicit microphone permission flow, so that invoking the assistant does not fail silently or bypass consent.
11. As a user, I want a deliberate assistant invocation to start the intended voice mode, so that an unexpected handler chooser does not interrupt every request.
12. As a user, I want a recognizable listening indicator and a way to cancel, so that I know when capture is active.
13. As a user, I want leaving or dismissing the assistant to stop capture, so that audio does not continue in the background.
14. As a user, I want activity recreation and repeated invocations handled safely, so that they do not reopen or duplicate microphone capture unexpectedly.
15. As a user, I want a locked watch to protect my Chat contents and actions, so that assistant invocation does not bypass the lock screen.
16. As a user, I want existing voice/live-voice/read-aloud choices honored or differences explained, so that behavior does not silently depend on the entry route.
17. As a user, I want the current configured Chat/call-target semantics preserved, so that assistant setup does not create or replace a Bot Chat.
18. As a user, I want phone, Gateway, recognition and permission failures distinguished, so that I can fix the real prerequisite.
19. As a user, I want to change back to another assistant through system settings, so that the feature is reversible without uninstalling Herald.
20. As a user, I want normal Herald app, tile and complication behavior preserved when Herald is not the default assistant, so that opting out has no unrelated effect.
21. As a user, I want updates to preserve consent without silently reselecting Herald, so that the operating system remains authoritative.
22. As a maintainer, I want model-specific evidence and narrowly scoped changes, so that a reported Samsung success does not regress OnePlus or imply universal support.
23. As a contributor, I want to collaborate with #251/#259 rather than duplicate them, so that testing and implementation effort help the existing work.

## Implementation Decisions

These are recommendations for maintainer review, not claims of decisions accepted upstream.

- Extend/review the existing native Wear OS feature rather than propose another standalone assistant app. The issue and PR already contain an ASSIST activity entry, a voice-interaction service/session, a voice-launch activity and setup UI.
- Treat operating-system role selection as the default-assistant on/off authority. Avoid a second master Boolean which can disagree with Android or leave the selected assistant disabled. Any future component-disabling option must address both activity and service/session paths and safe handoff to another assistant; it is not a trivial manifest toggle.
- Keep three concepts distinct in UI/state: Herald selected as assistant, OEM hardware gesture configured, and microphone/voice readiness. Only the first can be inferred from role ownership.
- Prefer supported, resolvable settings navigation. A generic role request is not a guaranteed fallback on every Wear OS build. Handle inability to navigate with usable instructions and no fake success.
- Refresh authoritative system state on lifecycle resume as well as settings-activity return. Do not persist a local "selected" truth or claim that the role guarantees button routing.
- Keep normal launch passive and deliberate assist/voice-shortcut launches explicit. Do not consume arbitrary incoming intent destinations, copy assist screen context unnecessarily, or add wake-word/audio privileges.
- Preserve existing lock-screen protections; withholding showWhenLocked alone is not a substitute for observing actual locked-session behavior. Test that transcript, recording, Chat access and actions remain protected.
- Document and test behavior differences between role-based session and activity-based launch. At inspected PR revision the role session records audio for the existing relay, while the talk activity retains its normal voice/recognizer decision; do not claim they honor identical preferences without checking or aligning them with the author.
- Investigate any resolver chooser before remediation: capture the exact originating intent, eligible handlers and preceding invocation path. Distinguish assistant selection from speech recognition and keyboard input. Do not silently force an OEM speech package, tell the user to select Always, or suppress a chooser by changing unrelated defaults.
- Reuse the existing phone relay, audio permissions, Chat identity and configured call-target behavior. Do not absorb the separate assistant-Profile proposal (#134) or default-call-target feature (#174) into this contribution.
- For this user's eventual migration, keep the experimental bridge separate until a native released or appropriately signed test pair is available. Selecting native Herald and removing the bridge are explicit, reversible actions; do not install a separately signed watch build over the official app and break Data Layer pairing.
- Source changes should be minimal and idiomatic to the upstream Kotlin/Compose/Gradle project. Local tooling/research and personal device baselines do not belong in the focused upstream patch.

## Testing Decisions

### Proposed primary seam

Test the complete user-visible journey: Assistant settings → actual system selection → configured physical gesture → native Herald capture → existing phone/Gateway Turn and Reply → change assistant back. This is the highest useful boundary. Component/intent and lifecycle tests support that journey but do not substitute for it.

Please confirm this acceptance seam before implementation or posting the final contribution scope; no new feature code is being written as part of this spec.

### Supporting tests and device evidence

- Reuse/extend the PR's assist-entry tests to distinguish plain launch, deliberate ASSIST, tile/complication and OEM voice-launch entry.
- Exercise role unavailable, settings unavailable, denied/non-requestable request, canceled setup, role changed outside Herald and refresh on resume. Assert user-visible state and navigation outcomes, not helper implementation.
- Add native session/activity lifecycle checks for repeated invocation, permission denial, recreation, hide/dismiss, recording cancellation and lock state. Explicitly test no duplicate/background capture.
- Before real speech testing, use safe interception/instrumentation to validate the actual dispatched route. Then conduct a consented physical hold, intelligible utterance and real Reply; label each result separately.
- Reproduce and identify the Galaxy Watch7 handler chooser before assigning a cause. Our bridge observation is a lead, not a demonstrated defect in PR #259.
- Test native role/session and activity shortcut separately, including the effect of existing voice/live-voice preferences and provider availability. A raw ASSIST launch does not verify a hardware button.
- Verify ordinary Herald/tile/complication behavior after switching away, and no automatic reselection on app update or restart. Verify OEM button restoration guidance without silently changing other assistants.
- Minimum reporting matrix: OnePlus author's existing evidence retained as author-reported; native Samsung Watch7 run needed; Pixel Watch/other Wear OS marked unverified until device evidence exists. Different OEM/OS combinations are not simulated success data.
- Follow CONTRIBUTING: relevant watch unit/lint/build tasks plus the prescribed shared/app CI tasks; real device/Gateway use; small/narrow-screen and theme checks where UI changes; sanitized screenshots attached to PR discussion, not committed to the repository. Never include private Chats, Prompts, Gateway addresses or device secrets.

## Out of Scope

- A duplicate upstream feature issue or competing implementation of #251/#259.
- Guaranteeing every Wear OS watch, changing OEM reserved button policies, root, hidden-setting writes, accessibility remappers, or default-assistant takeover.
- Wake words, always-on recording, Google feature parity, direct watch-to-Gateway mode, new credentials/accounts, Profile provisioning or call-target redesign.
- Shipping the experimental bridge/custom APK build scripts as the normal public feature.
- Automatically choosing a speech-recognition provider or changing Samsung keyboard defaults to hide an uninvestigated chooser.

## Further Notes

### Contribution workflow

1. Search/read existing work: completed; #251 and #259 are the relevant feature and implementation. #134 and #174 are related but separate.
2. Share a concise collaborative comment on #251 (and coordinate with the PR author), offering Samsung Watch7 validation and the setup/disable acceptance gaps. Do not open a duplicate issue or imply authorship of the existing feature.
3. Let maintainers/author agree the smallest useful contribution: device-test report, review follow-up, documentation or a focused code fix. A test report may be the best first contribution; coding is not required to help.
4. If code is requested, use a clean focused branch against the agreed upstream base, use Area: commit subjects, link #251 and coordinate branch ownership rather than send the entire experimental fork PR. One feature/fix per PR; update the ROADMAP only for work actually completed; permit maintainer edits.
5. Publish actual test results and remaining unverified devices. Do not mark a patch merge-ready based only on our bridge experiment or reported tests from another contributor.

### Evidence sources

- [Existing upstream issue #251](https://github.com/Giton22/herald/issues/251).
- [Existing upstream PR #259 and its reported test evidence](https://github.com/Giton22/herald/pull/259), inspected at revision `cd3223c527f7d8153efc202b4f29d9b09128a098`.
- [Upstream contribution guidelines](https://github.com/Giton22/herald/blob/master/CONTRIBUTING.md), retrieved through the GitHub API during this task.
- Local experiment evidence and primary-source citations: `watch-assistant-bridge-feasibility.md`, `watch7-firmware-routing.md` and `watch-bridge-device-validation.md` in the same research collection. They document a separate bridge experiment, not native-PR acceptance.
- [Cross-device primary-source evidence](upstream-watch-assistant-cross-device.md), including Android/AOSP role and settings contracts, first-party Pixel and Samsung guidance, and the pinned native PR sources. Research supports OS-owned opt-in/opt-out and does not establish untested third-party hardware support.
- [Android assistant qualification](https://developer.android.com/reference/androidx/core/role/RoleManagerCompat#ROLE_ASSISTANT), [voice-input settings contract](https://developer.android.com/reference/android/provider/Settings#ACTION_VOICE_INPUT_SETTINGS), [Pixel Watch assistant gesture](https://support.google.com/googlepixelwatch/answer/12677020?hl=en), and [Samsung assistant/button guidance](https://www.samsung.com/us/support/answer/ANS10003405/). These establish platform/OEM boundaries, not native Herald acceptance on every model.
