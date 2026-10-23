package dev.herald.voicebridge;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.TextView;

/** One-shot, permissionless handoff. Herald owns consent, recognition and chat identity. */
public final class AssistActivity extends Activity {
    private static final String SAVED_ERROR = "visible_error";
    private String visibleError;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        if (state == null) {
            handoff();
        } else {
            String saved = state.getString(SAVED_ERROR);
            showError(saved != null ? saved : "Voice handoff was interrupted. Invoke the assistant again to retry.");
        }
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        state.putString(SAVED_ERROR, visibleError);
    }

    @Override protected void onNewIntent(Intent incoming) {
        super.onNewIntent(incoming);
        setIntent(incoming);
        handoff();
    }

    private void handoff() {
        // Never copy assistant context, URI grants, caller flags or arbitrary extras.
        Intent herald = new Intent()
                .setClassName("dev.herald.android", "dev.hermeskotlin.wear.MainActivity")
                .putExtra("listen", true)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP
                        | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        try {
            startActivity(herald);
            finish();
        } catch (ActivityNotFoundException missing) {
            showError("Herald is not installed or its voice entry is unavailable. Install the official Herald watch app.");
        } catch (SecurityException denied) {
            showError("Herald cannot be opened. Check that the official Herald watch app is enabled and supports external voice launch.");
        }
    }

    private void showError(String message) {
        visibleError = message;
        TextView error = new TextView(this);
        error.setText(message);
        error.setGravity(Gravity.CENTER);
        error.setPadding(32, 32, 32, 32);
        setContentView(error);
    }
}
