package dev.herald.voicebridge.tests;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.ActivityNotFoundException;
import android.content.ComponentName;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;

/** Separate test APK: intercept every outgoing start before any target can run. */
public final class HandoffInstrumentation extends Instrumentation {
    private final List<Intent> outgoing = new ArrayList<Intent>();
    private String failure;
    private volatile boolean completed;

    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        start();
    }

    @Override public void onStart() {
        Bundle report = new Bundle();
        ActivityMonitor guard = new ActivityMonitor() {
            @Override public ActivityResult onStartActivity(Intent intent) {
                if ("dev.herald.voicebridge".equals(intent.getPackage())
                        || (intent.getComponent() != null && "dev.herald.voicebridge".equals(
                                intent.getComponent().getPackageName()))) return null;
                outgoing.add(new Intent(intent));
                if ("missing".equals(failure)) throw new ActivityNotFoundException("Test denial");
                if ("security".equals(failure)) throw new SecurityException("Test denial");
                // Block ALL other starts, including a regressed implicit launch.
                return new ActivityResult(Activity.RESULT_CANCELED, null);
            }
        };
        addMonitor(guard);
        Thread watchdog = new Thread(new Runnable() {
            @Override public void run() {
                android.os.SystemClock.sleep(45000);
                if (!completed) {
                    Bundle timedOut = new Bundle();
                    timedOut.putString("stream", "FAIL: boundary instrumentation exceeded 45s; no target starts allowed.\n");
                    finish(Activity.RESULT_CANCELED, timedOut);
                }
            }
        }, "bridge-test-timeout");
        watchdog.setDaemon(true);
        watchdog.start();
        try {
            assertResolves("android.intent.action.ASSIST");
            assertResolves("android.intent.action.VOICE_ASSIST");
            launchAndCheck("android.intent.action.ASSIST");
            launchAndCheck("android.intent.action.VOICE_ASSIST");
            failure = "missing";
            Activity warm = startActivitySync(incoming("android.intent.action.ASSIST"));
            waitForIdleSync();
            check(!warm.isFinishing(), "Missing target must leave a visible error");
            check(text(warm.getWindow().getDecorView()).contains("not installed"), "Missing-target error");
            failure = null;
            final Activity retained = warm;
            final int before = outgoing.size();
            runOnMainSync(new Runnable() {
                @Override public void run() {
                    // Framework lifecycle delivery, exercising the retained activity's onNewIntent.
                    callActivityOnNewIntent(retained, incoming("android.intent.action.VOICE_ASSIST"));
                }
            });
            waitForIdleSync();
            check(outgoing.size() == before + 1, "Warm activity must forward exactly once");
            assertOutgoing(outgoing.get(before));
            check(warm.isFinishing(), "Warm handoff must finish bridge");
            failure = "security";
            Activity denied = startActivitySync(incoming("android.intent.action.ASSIST"));
            waitForIdleSync();
            check(!denied.isFinishing(), "Denied target must leave a visible error");
            check(text(denied.getWindow().getDecorView()).contains("cannot be opened"), "Security error");
            runOnMainSync(new Runnable() { @Override public void run() { denied.finish(); } });
            report.putString("stream", "PASS: assist resolution, cold/repeated handoff, warm lifecycle, missing/security errors; ALL Herald starts blocked.\n");
            completed = true;
            finish(Activity.RESULT_OK, report);
        } catch (Throwable problem) {
            completed = true;
            report.putString("stream", "FAIL: " + problem.toString() + "\n");
            finish(Activity.RESULT_CANCELED, report);
        } finally {
            removeMonitor(guard);
        }
    }

    private Intent incoming(String action) {
        return new Intent(action).setPackage("dev.herald.voicebridge")
                .addCategory(Intent.CATEGORY_DEFAULT)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra("untrusted", "must not escape")
                .putExtra("listen", false);
    }

    private void assertResolves(String action) {
        check(getTargetContext().getPackageManager().resolveActivity(incoming(action),
                PackageManager.MATCH_DEFAULT_ONLY) != null, "Public action must resolve: " + action);
    }

    private void launchAndCheck(String action) {
        int before = outgoing.size();
        Activity bridge = startActivitySync(incoming(action));
        waitForIdleSync();
        check(outgoing.size() == before + 1, "Cold invocation must forward exactly once");
        assertOutgoing(outgoing.get(before));
        check(bridge.isFinishing(), "Successful handoff must finish bridge");
    }

    private void assertOutgoing(Intent actual) {
        check(new ComponentName("dev.herald.android", "dev.hermeskotlin.wear.MainActivity")
                .equals(actual.getComponent()), "Must target official Herald explicitly");
        Bundle extras = actual.getExtras();
        check(extras != null && extras.size() == 1 && Boolean.TRUE.equals(extras.get("listen")),
                "Only boolean listen=true may cross boundary");
        check(actual.getClipData() == null && actual.getData() == null, "No inherited assist context");
        int expected = Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP
                | Intent.FLAG_ACTIVITY_SINGLE_TOP;
        check(actual.getFlags() == expected, "Cold/warm task reuse flags");
    }

    private static String text(View view) {
        String result = view instanceof TextView ? ((TextView) view).getText().toString() : "";
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) result += text(group.getChildAt(i));
        }
        return result;
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
