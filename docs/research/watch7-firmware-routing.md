# Watch7 Home-button long-hold: local firmware evidence

## Conclusion

**`setting_home_key_long_press` is a mode selector, not an arbitrary flattened-component launcher in the inspected policy.** Its supported assistant-mode token is exactly `googlevoiceassistant/googlevoiceassistant`. Despite that legacy name, this mode invokes the general assistant entry point, not a hard-coded Google activity/service. The Bixby-looking value is also a selector: policy dispatches to a different, fixed Bixby key service, not to the named `WinkService`.

The firmware-supported route worth testing for a third-party bridge is therefore **assistant-role selection plus Samsung's assistant long-hold mode**, with an eligible assistant activity/service. Do not put a guessed bridge component in the Samsung global setting: the observed catch-all selects the power menu. This is a static-routing finding, **not proof that a third-party bridge receives a real button hold**. No device access or settings changes were performed for this investigation.

## Evidence scope and reproducibility

Read-only inspection of DEX instructions from the supplied local files under `~/.local/state/herald-voice-bridge/firmware/`:

| File | SHA-256 |
| --- | --- |
| `settings.apk` | `d9b7e7f641d4bdf45831a5c7223a8e3b13a6e6f60a19bf1962e98a1a59516270` |
| `services.jar` | `14a50332a1c4d5d87a3da9e5691e9e6dce605ef74b19e43ce1427fb3e5cfbfed` |

Tool: Androguard **4.1.4**, obtained through `uv run --with androguard` using the Python package index configured for uv; no standalone decompiler downloaded, no Java toolchain required, no system install or license acceptance. ZIP-contained DEX files were parsed directly and method instructions inspected; this is not reconstructed original Java source. All cited Settings methods below are in `settings.apk/classes.dex`; policy methods are in `services.jar/classes.dex`; voice-interaction methods are in `services.jar/classes2.dex`. Names are the observed optimized DEX names, including R8 synthetic/merged classes. Findings here are paraphrased; no proprietary source or binary is included.

This identifies these exact artifacts, not all Watch7 firmware revisions. Framework client implementation, SystemUI's final assistant dispatcher, role-controller qualification implementation, and the bridge APK were outside this two-file inspection.

## Samsung selector consumer and actual policy branches

Sources: `com.android.server.policy.PhoneWindowManagerExt.init(Injector)` and `PhoneWindowManagerExt$SettingsObserver$$ExternalSyntheticLambda0.accept(Object)`.

`init` registers a global-setting observer. Its callback reads `Settings.Global` key `setting_home_key_long_press`, stores it in `mPowerKeyLongAppInfo`, and selects `PhoneWindowManager.mLongPressOnPowerBehavior` by exact string equality:

| Exact observed value | Behavior assigned |
| --- | --- |
| `com.samsung.android.bixby.agent/com.samsung.android.bixby.WinkService` | `101`, Bixby branch |
| `poweroff/poweroff` | `1`, global-actions/power-menu branch |
| `googlevoiceassistant/googlevoiceassistant` | `5`, assistant branch |
| Any other value, including null | `1`, global-actions/power-menu branch |

There is no conversion of this global setting into a generic activity/service component in this consumer. References to `mPowerKeyLongAppInfo` in the inspected methods are caching, comparisons, and diagnostic logging, not generic dispatch.

Source: `PhoneWindowManager$BackKeyRule.<init>(PhoneWindowManager,int)` and `.onLongPress(long,KeyEvent)`. R8 merged multiple key rules under this misleading class name. The power-rule constructor branch registers key code **26**; its long-hold branch resolves the power behavior and:

- For **101**, uses Samsung-keyboard dictation if applicable; otherwise constructs long-press `BixbyServiceParams` and calls `BixbyService.startService` subject to lock-screen and other guards.
- For **5**, also allows Samsung-keyboard dictation/system-key interception; otherwise calls `PhoneWindowManager.launchAssistAction` with invocation type **6** and the event time.
- For **1**, requests global actions.

Source: `PhoneWindowManager.launchAssistAction(int,int,String,long)`. After setup checking, it constructs assistant invocation arguments and calls `SearchManager.launchAssist(Bundle)` when that service exists; the fallback calls `IStatusBar.startAssist(Bundle)`. **This method does not hard-code a Google package or use the Samsung setting as an explicit target.** Its downstream client/SystemUI implementation was not supplied, so final activity-versus-voice-session dispatch is not established here.

Source: `PhoneWindowManager.getResolvedLongPressOnPowerBehavior()`. Factory/test/setup/touch-lock conditions can override the configured behavior; assistant mode additionally checks provisioning. The separate `clockwork_long_press_to_assistant_enabled` check is attached to behavior **4**, not the observed selector's behavior **5**. Do not conflate those modes.

### Bixby is explicitly special-cased

Sources: `com.android.server.policy.BixbyService.<init>`, `getIntentBixbyService(BixbyServiceParams)`, and `startService(BixbyServiceParams)`.

The constructor parses fixed component constants:

- Long: `com.samsung.android.bixby.agent/com.samsung.android.bixby.BixbyKeyLService`
- Short: `com.samsung.android.bixby.wakeup/com.samsung.android.bixby.BixbyKeySService`

The intent builder chooses the long service for long-press/from-long-press events, sets the component, and attaches `KEYEVENT` (and `KEY_COMBINATION` where applicable). Dispatch uses `Context.startServiceAsUser` for the system user, with setup, keyguard, water-lock, factory, and system-key guards. This is **fixed Bixby-specific component dispatch**, not generic dispatch of `mPowerKeyLongAppInfo` and not direct invocation of `WinkService`.

## Settings writers/readers

Unless expanded below, these classes are under `com.samsung.android.clockwork.settings`.

- `advanced.homekey.StPressAndHoldModel.getPressAndHoldString` / `setPressAndHoldString`: direct global-key read/write. `getKeyList` constructs the Google-token/Bixby-token/power-token menu subject to availability; `checkCurrentValue` repairs unavailable assistant choices to Bixby or power off. `getPressAndHoldLabel` uses the selected assistant package's application label for the Google-token mode.
- `advanced.homekey.StAdvancedHomePressAndHoldFragment.$r8$lambda$Xm9sN0L9VBBKP4BIIuszS1Cah-s`: preference-click writer through the model. `advanced.sync.StDataLayerPressHoldHomeManager.handleSyncData`: paired-settings writer through that model. `bnr.helper.StBnrAdvancedItemHelper.setPressAndHoldHomeKey`: restore writer with availability fallback.
- `reset.StResetSettings.resetAllSettings`: directly writes the Bixby selector.
- `btngesture.gestures.StRaiseToTalkModel.setRaiseToTalkType`: unless long-hold is already power off, synchronizes `bixby` to the Bixby selector and `gemini` to the Google-token selector. `service.StDataLayerListenerService.onMessageReceived` also maps those assistant choices through the model and checks availability.
- `service.StDataLayerListenerService$2.onChange`: setup-completion/detach handling can replace Bixby with power off. `service.StDeviceOwnerChangedReceiver.onReceive`: device-owner-change handling can likewise replace Bixby with power off.
- Other observed consumers are UI, synchronization, or backup: `advanced.homekey.StAdvancedHomekeyFragment.onResume/updatePressAndHold` and its observer; `btngesture.StBtnGestureFragment.onCreatePreferences/updateAll$10`; `advanced.sync.StDataLayerPressHoldHomeManager.<init>/sendSyncDataStringOnly`; `bnr.helper.StBnrAdvancedItemHelper.getPressAndHoldHomeKey`. These are not button-launch dispatchers.

`google.StGoogleAssistModel.<init>/isGaExist` provides a separate availability gate via a resource-configured package/action and metadata resolver. Its resource values were not decoded here; thus generic dispatch does not imply the UI exposes assistant mode with Google removed.

## Default assistant is separate, role-backed state

Source: `common.util.DigitalAssistantAppUtils.getSelectedAssistantApp` / `setAssistantApp`. Settings reads `RoleManager.getDefaultApplication` and writes `RoleManager.setDefaultApplication` for exactly `android.app.role.ASSISTANT`. The writer is called by `apps.digitalassistant.StDefaultDigitalAssistantFragment$4.onPreferenceClick` and `advanced.sync.StDataLayerDigitalAssistantManager.handleSyncData`. Those paths do not write the Samsung button selector.

Source: `DigitalAssistantAppUtils.getDigitalAssistantPackages`. Candidate discovery includes qualifying voice-interaction services and **exported activities resolving `android.intent.action.ASSIST`**. Thus the Settings code is not a Google-only assistant-package picker and does not exclusively require a voice-interaction service. Actual role-controller acceptance remains untested.

Source: `com.android.server.voiceinteraction.VoiceInteractionManagerService$VoiceInteractionManagerServiceStub$RoleObserver.onRoleHoldersChanged`:

- Reads holders of `android.app.role.ASSISTANT` for the affected user.
- With no holder, clears secure `assistant` and `voice_interaction_service`.
- For a qualifying voice interactor, derives the selected service component and writes secure assistant/interactor state; recognition-service validation can leave that state empty.
- Otherwise queries `android.intent.action.ASSIST` **within the role-holder package**, writes the resolved activity's short flattened name to secure `assistant`, and clears secure `voice_interaction_service`.

Consequently, an assistant activity together with an empty `voice_interaction_service` is an explicitly represented firmware state, not by itself evidence of misconfiguration. Additional secure-assistant maintenance writers exist in the stub's package monitor `$2.onSomePackagesChanged` and synthetic `-$$Nest$mresetServicesIfNoRecognitionService` recovery method.

Source: `PhoneWindowManagerExt$SettingsObserver$$ExternalSyntheticLambda0.accept` also reads secure `assistant` for the current user into `mAssistantAppName`. In the inspected power-long-hold branch this field supplies diagnostic attribution after launching assist; it does **not** override a Bixby selector. `RoleServicePlatformHelperImpl.getLegacyRoleState` reads legacy assistant state for role migration; `AudioService.updateAssistantUIdLocked` consumes assistant state for audio identity, not button routing.

## Interpretation of the supplied live baseline

The parent supplied (not independently collected here): global selector = Bixby/WinkService token; assistant role and secure `assistant` = Google; secure voice service empty. Later parent-supplied policy diagnostics identify `LONG_PRESS_POWER_BIXBY_VOICE`, the same Bixby selector in `mPowerKeyLongAppInfo`, and separate no-op Home / Samsung Pay-or-workout stem behaviors.

These observations fit the static evidence: Samsung's labeled Home-button hold follows the **power-key policy**, and selecting a default assistant alone does not replace the Bixby button mode. A future authorized test should select an eligible bridge as the assistant and select Samsung's assistant long-hold mode, then verify real key-down/up dispatch and bridge invocation, including lock-screen/keyboard guards and restoration. Neither arbitrary component assignment to the global key nor successful role assignment alone establishes that result.
