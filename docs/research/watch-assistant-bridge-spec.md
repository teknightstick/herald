## Problem Statement

The user wants to hold the orange Home button on a Samsung Galaxy Watch7 and immediately speak to Hermes, instead of invoking Google or Bixby. Opening Herald without starting voice input, or substituting a double press, is not equivalent. The user authorized researched, reversible implementation while the watch remains connected on its charger.

## Solution

Deliver the closest supported, reversible assistant replacement: a small separately installed Herald Voice Bridge which forwards an assistant invocation into the official Herald watch application's existing voice flow. Preserve the official watch and phone applications, their signing relationship, the user's gateway configuration, and the ability to restore the previous assistant and button behavior.

Treat Android assistant selection, Samsung Home-button routing, cross-application voice activation, and phone/gateway availability as separate capabilities to prove. A generic Android intent launch does not establish physical-button success.

## User Stories

1. As a watch wearer, I want holding Home to start Herald voice, so that I can speak to Hermes without navigating app menus.
2. As a watch wearer, I want the existing Herald live-voice preference respected, so that live voice starts only when enabled and supported.
3. As a watch wearer, I want normal speech input otherwise, so that unsupported live voice does not prevent asking a question.
4. As a watch wearer, I want the same behavior with Herald closed or already open, so that I need not manage application lifecycle.
5. As a watch wearer, I want microphone permission handled by Herald, so that a launcher does not acquire unnecessary audio access.
6. As a watch wearer, I want connection problems surfaced by Herald, so that the bridge does not claim an unavailable agent is listening.
7. As a watch wearer, I want my existing chat selection and conversation continuity preserved, so that a button press does not create a replacement Bot Chat.
8. As a watch wearer, I want an intelligible failure when Herald is absent or incompatible, so that setup problems do not look like a dead button.
9. As a watch owner, I want official Herald updates and phone pairing preserved, so that this shortcut does not create a custom-signing maintenance burden.
10. As a watch owner, I want Google and Bixby left installed, so that I can restore their behavior without reinstalling anything.
11. As a watch owner, I want original assistant and Samsung button values saved, so that rollback is exact rather than guessed.
12. As a watch owner, I want the bridge to have no network, microphone, accessibility, or notification-listener privileges, so that it only launches voice input.
13. As a watch owner, I want setup and rollback instructions, so that I can recover after an update or removal.
14. As a watch owner, I want Samsung restrictions reported honestly, so that a simulated invocation is not mistaken for a working hardware shortcut.
15. As a watch owner, I want no background listening, so that this replacement remains explicitly button-activated.
16. As a maintainer, I want reproducible builds, tests and device evidence, so that a successful experiment can become maintainable software.
17. As a maintainer, I want a safely signed separate application, so that the official Herald signing key is not needed.
18. As a watch wearer, I want no unsolicited prompt sent during unattended testing, so that ambient speech is not submitted as an agent instruction.

## Implementation Decisions

- Build a separate, clearly named Wear OS bridge with its own application identifier. Do not modify or re-sign the official Herald APK or change phone/gateway configuration.
- Use the existing exported Herald activity's boolean listening entry point. Source inspection identifies this as the same flow used by Herald's microphone shortcut, which chooses supported live voice or speech recognition/recording. Verify the contract on the installed release before claiming compatibility.
- Begin with activity-based Android assistant handling because this device's current assistant uses that mechanism. Add voice-interaction services only if primary-source requirements or actual device tests establish that need. Do not invent an unnecessary always-running service.
- Advertise standard assist and voice-assist intents. Eligibility for the Android assistant role and eligibility for Samsung's Home-button configuration remain explicit feasibility gates, not assumptions.
- Preserve and read back the original assistant role, secure assistant component, voice-interaction component, and Samsung button configuration. Change only the narrow settings necessary; never bypass role qualification, disable Google/Bixby, root the watch, or grant broad privileges.
- The bridge requests no audio or network permission and delegates recognition, microphone consent, gateway access and chat identity to Herald.
- Handle unavailable or incompatible Herald with a visible error, not a silent fallback to another assistant or a retry loop.
- The bridge must finish cleanly after a successful handoff. Investigate lifecycle interference before deciding final flags; avoid an overlay or lifecycle transition which immediately stops Herald's recording or call.
- Leave gateway protocol and Bot Chat continuity unchanged, consistent with the repository's proposed architecture decisions.
- Keep builds isolated from the main multiplatform application where practical. Use independently licensed user-local tools, or surface explicit SDK license acceptance as a blocker; do not accept agreements on the user's behalf.
- Plan and execute through a single integration branch with separate implementation ticket branches/worktrees. Preserve unrelated untracked domain and agent guidance.

## Testing Decisions

- Primary seam: Android assistant invocation through the bridge into observable Herald voice entry. This tests externally visible behavior rather than private helpers or invented internal collaborators.
- First tracer bullet: an installed assistant-capable activity can resolve and hand off to official Herald while remaining separately signed. Test the public invocation contract before expanding the implementation.
- Exercise cold and warm Herald launches, missing Herald, deliberate launch failure, and permission/connection limitations. Avoid fabricating device states or disrupting the paired phone to test edge cases.
- Repeated activation must not create a bridge loop or multiple independent bridge tasks. Any microphone start during testing must be explicitly bounded and immediately canceled; no ambient recording or test prompt submission.
- Validate Android role selection and Samsung button routing separately, including readback after every write. If privileged role assignment is used for local setup, do not claim the normal user selector is supported without checking it.
- A shell-generated assistant action is only an integration check. A synthetic long key event is only a firmware dispatch experiment. Neither replaces the user's physical Home-button hold acceptance test.
- Existing watch tests cover presentation behavior and do not establish Android assistant eligibility. Add only tests at the agreed assistant-launch boundary; do not broaden scope into watch UI or gateway refactoring.
- Verify rollback to the exact saved assistant/button state, then reapply the candidate only if safe and useful. Retain a clear distinction between restored, candidate-configured, and hardware-confirmed states.
- Record commands, actual results, source references, APK checksum and remaining manual acceptance checks without storing pairing codes, device serials, gateway credentials or speech content in public issues.

## Out of Scope

- Replacing the watch operating system, root access, disabling Samsung Wallet, accessibility interception, or remapping the Back button.
- Wake words, always-on microphones, Google feature parity, direct watch-to-gateway mode, a replacement recognition engine, or new gateway services.
- Changing chats, starting fresh, new credentials/accounts, phone installation or gateway networking changes.
- Claiming success from build/install alone or calling a double-press shortcut completion of the hold-to-talk requirement.

## Further Notes

Verified baseline: Galaxy Watch7 model family SM-L310, Android 16 / API 36, One UI property 80000, official Herald 0.13.0 installed and verified. Android assistant role and secure assistant point to Google; no voice-interaction service was configured. Samsung's separate Home long-press setting points to Bixby, proving that the two layers must be investigated separately. Original device settings are saved locally for rollback, not published.

Primary-source feasibility research is running and will be linked with its conclusions. No claim of third-party Samsung hardware support is made yet. The user's direction to infer the desired assistant replacement and proceed authorizes the proposed test seam and a small dependency-ordered breakdown without further interactive planning rounds. Actual physical button confirmation remains pending until the user returns.
