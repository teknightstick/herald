# Watch bridge: isolated build toolchain

## Status

**JDK and independently licensed APK tools installed and verified; a throwaway Java Activity APK targeting 36 / minimum 30 was compiled, resource-linked, signed, and signature-verified without accepting an Android SDK license.** No bridge app sources or watch/build files were changed. No device commands, Gradle build, system package installation, sudo, shell-profile change, or global environment change was made.

The SDK-package investigation below is retained for provenance: those SDK archives remain blocked and were not downloaded. That gate does **not** apply indiscriminately to separately published open-source Maven artifacts. See **Verified independent Maven toolchain** below for the working alternative.

Toolchain root:

`/home/godstopper/.local/share/herald-voice-bridge-toolchain`

The directory is self-contained and removable. Existing unrelated repository files were preserved.

## Working Java tools

Official Eclipse Temurin JDK 21, Linux x64 HotSpot, release `jdk-21.0.13+9`:

| Tool | Absolute binary path | Executed verification |
| --- | --- | --- |
| Java | `/home/godstopper/.local/share/herald-voice-bridge-toolchain/jdk-21.0.13+9/bin/java` | `-version`: OpenJDK 21.0.13, Temurin-21.0.13+9, exit 0 |
| Java compiler | `/home/godstopper/.local/share/herald-voice-bridge-toolchain/jdk-21.0.13+9/bin/javac` | `-version`: javac 21.0.13, exit 0 |
| JAR packager | `/home/godstopper/.local/share/herald-voice-bridge-toolchain/jdk-21.0.13+9/bin/jar` | `--version`: jar 21.0.13, exit 0 |
| Key utility | `/home/godstopper/.local/share/herald-voice-bridge-toolchain/jdk-21.0.13+9/bin/keytool` | `-help`: tool starts successfully, exit 0; no signing key generated |

Raw command results are stored in:

`/home/godstopper/.local/share/herald-voice-bridge-toolchain/verification.json`

These are startup/version checks, not an APK-build verification. Java is intentionally not added to PATH.

## Download provenance and integrity

### Downloaded JDK

Metadata requested from the official Adoptium API:

`https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=x64&image_type=jdk&os=linux&vendor=eclipse`

Saved metadata:

`/home/godstopper/.local/share/herald-voice-bridge-toolchain/downloads/adoptium-jdk21.json`

Artifact origin returned by that API:

`https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9/OpenJDK21U-jdk_x64_linux_hotspot_21.0.13_9.tar.gz`

Official checksum origin:

`https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.13%2B9/OpenJDK21U-jdk_x64_linux_hotspot_21.0.13_9.tar.gz.sha256.txt`

Archive and checksum file are retained under the toolchain's `downloads/` directory with those original filenames. The computed archive SHA-256 matched **both** the official API metadata and checksum file:

```text
d7f5d5cf865a2902b70ff549b97586a7d3f234e016f041ab447ea740c7d66d1c
```

Archive size reported by the API: 207858352 bytes. Archive extraction used Python's `tarfile` data filter. This is checksum verification against the official HTTPS publisher sources, not independent GPG signature authentication.

The initial Python urllib request received HTTP 403; curl successfully retrieved official metadata and release assets. No third-party mirror or proxy was used.

### Downloaded Android repository metadata, not SDK binaries

Official metadata origin:

`https://dl.google.com/android/repository/repository2-3.xml`

Saved at:

`/home/godstopper/.local/share/herald-voice-bridge-toolchain/downloads/repository2-3.xml`

This XML was retrieved over HTTPS. No independent checksum for the XML was obtained. It identifies these stable SDK packages and their publisher-provided SHA-1 values:

| Package | Official archive URL | Expected SHA-1 from XML | Download status |
| --- | --- | --- | --- |
| Android SDK Platform 36, revision 2 | `https://dl.google.com/android/repository/platform-36_r02.zip` | `2c1a80dd4d9f7d0e6dd336ec603d9b5c55a6f576` | Not downloaded: license gate |
| Android SDK Build-Tools 36.0.0, Linux | `https://dl.google.com/android/repository/build-tools_r36_linux.zip` | `b0b6376977657e8ad9b969bacf4093601da2c6fb` | Not downloaded: license gate |
| Android SDK Command-line Tools 23.0, Linux | `https://dl.google.com/android/repository/commandlinetools-linux-16111833_latest.zip` | `e025545c62a8e64c7559119566a569fb1dec5f60` | Not downloaded: license gate |

These SDK hashes are **expected values, not verified downloads**. SHA-1 is the checksum published in this XML; it is weaker than SHA-256. Exact package metadata came from the live repository XML rather than search snippets, which listed a different command-line-tools build.

## Android SDK license blocker

All three SDK packages declare `uses-license ref="android-sdk-license"`. The repository license's section 2.1 states:

> In order to use the SDK, you must first agree to the License Agreement. You may not use the SDK if you do not accept the License Agreement.

The official download page also says agreement is required before downloading:

`https://developer.android.com/studio#command-line-tools-only`

This is an acceptance requirement, not merely a public licensing notice. Direct public ZIP URLs do not remove it. Consequently, SDK binaries were neither downloaded nor executed, and no license-marker files were fabricated or copied. `sdkmanager --licenses` was not run and no answers were piped into a license prompt.

A review-only copy of the exact stable license text from the downloaded XML is available at:

`/home/godstopper/.local/share/herald-voice-bridge-toolchain/android-sdk-license.review-only.txt`

This file is **not** an SDK acceptance marker. The text in the XML ends with January 16, 2019.

`JAVA_HOME`, `ANDROID_HOME`, and `ANDROID_SDK_ROOT` were unset. No existing `licenses/android-sdk-license` marker was found in these candidate SDK roots:

- `/home/godstopper/Android/Sdk`
- `/home/godstopper/Android/sdk`
- `/home/godstopper/.android`
- `/home/godstopper/.local/share/android-sdk`
- `/home/godstopper/.local/share/android`
- `/opt/android-sdk`
- `/usr/lib/android-sdk`

This bounded check does not prove no license was ever accepted elsewhere. Explicit user acceptance or a confirmed existing accepted installation is needed before proceeding.

## Intended direct build layout after acceptance

The following are **planned paths, not installed or verified tools**:

```text
/home/godstopper/.local/share/herald-voice-bridge-toolchain/android-sdk/platforms/android-36/android.jar
/home/godstopper/.local/share/herald-voice-bridge-toolchain/android-sdk/build-tools/36.0.0/aapt2
/home/godstopper/.local/share/herald-voice-bridge-toolchain/android-sdk/build-tools/36.0.0/d8
/home/godstopper/.local/share/herald-voice-bridge-toolchain/android-sdk/build-tools/36.0.0/zipalign
/home/godstopper/.local/share/herald-voice-bridge-toolchain/android-sdk/build-tools/36.0.0/apksigner
/home/godstopper/.local/share/herald-voice-bridge-toolchain/android-sdk/cmdline-tools/23.0/bin/sdkmanager
```

After user acceptance, download and verify official archives against repository metadata, extract into the isolated layout, and test tool startup with process-local `JAVA_HOME` pointing to the installed JDK. The intended small Java build uses `javac`, `aapt2`, `d8`, ZIP/JAR packaging, `zipalign`, and `apksigner`; it does not require the root Herald Gradle build. Command-line tools are only needed for normal SDK/license management, not the direct APK assembly pipeline.

The SDK-distribution route above remains unverified and license-gated. It is not necessary for the restricted Java-only build demonstrated below.

## Verified independent Maven toolchain

All files are isolated under:

`/home/godstopper/.local/share/herald-voice-bridge-toolchain/independent`

No SDK archive was downloaded, no SDK license accepted, no `sdkmanager` invoked, and no SDK license markers created. These are separately published open-source artifacts, not a direct-download workaround for the SDK archives above.

### License provenance actually checked

| Artifact | Exact version | License evidence retained locally |
| --- | --- | --- |
| `com.android.tools.build:aapt2:linux` | `8.13.0-13719691` | Publisher `aapt2.pom` declares Apache-2.0; archive `NOTICE` contains Apache-2.0 and bundled component notices, preserved in `aapt2/NOTICE` and `notices/aapt2-linux/NOTICE`. |
| R8 including D8 | `8.13.17` | The downloaded JAR's own `LICENSE` explicitly grants BSD-3-Clause for non-library code and lists bundled dependency licenses; preserved in `notices/r8/LICENSE`. Current upstream license also saved as `R8-LICENSE`, but the embedded version is the artifact-specific authority. |
| `com.android.tools.build:apksig` | `8.13.0` | Publisher `apksig.pom` declares Apache-2.0; JAR `LICENSE` retained at `notices/apksig/LICENSE`. This is a library, not an `apksigner` executable. |
| `com.google.android:android` | `4.1.1.4` (API 16) | Maven Central `android.pom` declares Apache-2.0 and explicitly distinguishes its source-built binaries from EULA-restricted SDK binaries. It identifies `android-4.1.1_r4`. JAR includes framework `resources.arsc`, not just Java signatures. |

The Android stub artifact's POM states: “While the EULA for the Android SDK restricts distribution of those binaries, the source code is licensed under Apache 2.0 which allows compiling binaries from source and then distributing those versions.” This is publisher-provided provenance, not an independent reproduction of its source build. No newer Robolectric platform was needed.

Primary references:

- Official separately published AAPT2 download instructions: <https://developer.android.com/tools/aapt2#download_aapt2>
- AAPT2 POM: <https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/8.13.0-13719691/aapt2-8.13.0-13719691.pom>
- apksig POM: <https://dl.google.com/dl/android/maven2/com/android/tools/build/apksig/8.13.0/apksig-8.13.0.pom>
- Android stub POM: <https://repo.maven.apache.org/maven2/com/google/android/android/4.1.1.4/android-4.1.1.4.pom>
- Official R8 prebuilt distribution instructions: <https://r8.googlesource.com/r8/+/refs/heads/main/>
- R8 upstream BSD license: <https://r8.googlesource.com/r8/+/refs/heads/main/LICENSE>

Retain the downloaded licenses/notices if redistributing tools; bundled dependencies have their own notices. None of these inspected publication licenses requires the separate Android SDK agreement acceptance workflow. This is artifact provenance analysis, not legal advice.

### Installed artifacts, download URLs, and integrity

`artifact-urls.json` records exact origins; `integrity.json` records sizes, computed SHA-256, and publisher SHA-1 comparisons. The AAPT2, apksig, and Android JARs each matched their official HTTPS `.sha1` sidecar. R8 has a locally recorded SHA-256 only; no independent published checksum or signature was verified. SHA-1 matching provides limited transport/publisher consistency, not strong independent authentication.

| Local file under `independent/` | Download URL | Computed SHA-256 |
| --- | --- | --- |
| `aapt2-linux.jar` | <https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/8.13.0-13719691/aapt2-8.13.0-13719691-linux.jar> | `c1aebd96a144313da65de675cc1f59041b41a52e844228d311bb580ed830b0d9` |
| `r8.jar` | <https://storage.googleapis.com/r8-releases/raw/8.13.17/r8.jar> | `98b7741c0ed50bf86174bea93a62d1879e838fae6d7166fd4fac2787e11b3572` |
| `apksig.jar` | <https://dl.google.com/dl/android/maven2/com/android/tools/build/apksig/8.13.0/apksig-8.13.0.jar> | `c070ed1394629d74641aa0906f60b2ffa1ee77e6366a1f93437f59717b1aeb89` |
| `android.jar` | <https://repo.maven.apache.org/maven2/com/google/android/android/4.1.1.4/android-4.1.1.4.jar> | `84072541cbb711eff89f7277100ff854929a446dba7ceb1b195c340e0b4fd3cb` |

Working native binary: `independent/aapt2/aapt2` (relative to toolchain root). Java tools use the existing JDK, not a global install.

Executed startup checks:

```sh
T=/home/godstopper/.local/share/herald-voice-bridge-toolchain
"$T/independent/aapt2/aapt2" version
# Android Asset Packaging Tool (aapt) 2.20-13719691
"$T/jdk-21.0.13+9/bin/java" -cp "$T/independent/r8.jar" com.android.tools.r8.D8 --version
# D8 8.13.17
```

apksig was exercised through its real Java signing and verification APIs. `probe/SignProbe.java` is a retained, deliberately narrow adapter; its no-argument invocation prints usage. It is not the SDK's `apksigner` CLI.

### Actual end-to-end build and exact commands

The throwaway fixture lives outside the repository at `independent/probe/`. It contains one `Activity` using `Bundle` and `TextView`, a manifest with explicit exported launcher, and a compiled string resource. All app APIs and manifest attributes used exist at API 16 or earlier; the manifest explicitly selects minimum 30 and target 36.

Run the complete build, including signing and verification:

```sh
bash /home/godstopper/.local/share/herald-voice-bridge-toolchain/independent/probe/build-probe.sh
```

The retained script is the exact executed recipe, with these build commands (run after the fixture exists):

```sh
T=/home/godstopper/.local/share/herald-voice-bridge-toolchain
J="$T/jdk-21.0.13+9/bin"
I="$T/independent"
P="$I/probe"
mkdir -p "$P/out/classes" "$P/out/dex" "$P/out/host"
"$J/javac" --release 8 -cp "$I/android.jar" -d "$P/out/classes" "$P/src/probe/MainActivity.java"
"$J/jar" --create --file "$P/out/classes.jar" -C "$P/out/classes" .
"$J/java" -cp "$I/r8.jar" com.android.tools.r8.D8 --release --min-api 30 \
  --lib "$T/jdk-21.0.13+9" --lib "$I/android.jar" \
  --output "$P/out/dex" "$P/out/classes.jar"
"$I/aapt2/aapt2" compile --dir "$P/res" -o "$P/out/resources.zip"
"$I/aapt2/aapt2" link -I "$I/android.jar" --manifest "$P/AndroidManifest.xml" \
  --min-sdk-version 30 --target-sdk-version 36 "$P/out/resources.zip" -o "$P/out/unsigned.apk"
python3 -c 'import zipfile,sys; z=zipfile.ZipFile(sys.argv[1],"a",compression=zipfile.ZIP_DEFLATED); z.write(sys.argv[2],"classes.dex"); z.close()' \
  "$P/out/unsigned.apk" "$P/out/dex/classes.dex"
if [ ! -f "$P/probe.p12" ]; then
  "$J/keytool" -genkeypair -storetype PKCS12 -keystore "$P/probe.p12" \
    -storepass changeit -keypass changeit -alias probe -keyalg RSA -keysize 2048 \
    -validity 365 -dname 'CN=Throwaway Toolchain Probe'
  chmod 600 "$P/probe.p12"
fi
"$J/javac" -cp "$I/apksig.jar" -d "$P/out/host" "$P/SignProbe.java"
"$J/java" -cp "$P/out/host:$I/apksig.jar" SignProbe "$P/out/unsigned.apk" "$P/out/probe.apk" "$P/probe.p12"
"$I/aapt2/aapt2" dump badging "$P/out/probe.apk"
sha256sum "$P/out/probe.apk"
```

Signing adapter explicitly enables APK v2/v3, disables v1/v4, uses min SDK 30, and verifies against Android platform range 30–36. `probe.p12` is an intentionally throwaway local key with a public test password, **not a bridge/release signing identity**. No existing key was replaced.

Actual final execution (`probe/verification.log`) exited 0:

```text
verified=true v2=false v3=true errors=[] warnings=[]
package: name='org.herald.toolchainprobe' versionCode='1' versionName='0.0.1'
minSdkVersion:'30'
targetSdkVersion:'36'
application-label:'Toolchain probe'
launchable-activity: name='probe.MainActivity'
```

The verifier selects v3 for the checked platform range; its `v2=false` does not mean the v2 block is absent. A separate ZIP/signing-block inspection confirmed IDs `0x7109871a` (v2) and `0xf05368c0` (v3). The APK contains binary `AndroidManifest.xml`, stored `resources.arsc`, and DEFLATED `classes.dex`. The final stored resource data offset is 684, divisible by four. There are no native libraries. No separate `zipalign` binary is required for this particular verified layout; this is not a general replacement for native-library/page alignment requirements.

Final artifact:

`/home/godstopper/.local/share/herald-voice-bridge-toolchain/independent/probe/out/probe.apk`

Computed SHA-256:

`4884552b97a38637fa4466885f059262a26af9546a17f6b37c71cc6ee7b6eae7`

### Limits and issues found

- No remaining toolchain blocker for this minimal Java-only, old-API subset. Resource compilation/linking against the API 16 Maven platform worked with numeric target 36/minimum 30; no hand-written framework resource IDs were necessary.
- This does **not** provide API 36 compile-time classes/resources. New platform APIs, post-API-16 manifest attributes, AndroidX/Wear libraries, production desugaring, or a full SDK build need additional independently licensed artifacts and fresh verification (or an accepted SDK).
- Initial D8 run warned about missing `java.lang.Object` because this Maven Android JAR omits core Java classes. Providing the existing JDK as an additional `--lib` removed that warning. This is adequate for the demonstrated simple Java 8 bytecode, not a promise of arbitrary JDK API availability on Android.
- Initial resource link used overlay flag `-R`, which rejected a new string resource. Passing the compiled resource archive positionally fixed it. Use `-R` only when overlay semantics are intended.
- Remaining compiler notes: JDK 21 warns source/target 8 are obsolete; the host signing adapter calls a deprecated apksig API. Neither prevented execution.
- No APK was installed or launched, so runtime/Wear OS/bridge behavior is unverified. The probe is not the bridge implementation and is not Wear-specific.
- No repository watch/build app files were modified; this research document is the sole repository file changed by this investigation.

