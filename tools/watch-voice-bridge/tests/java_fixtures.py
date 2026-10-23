"""Minimal host lifecycle doubles, NOT Android/device behavior claims."""
SOURCES = {
    "android/os/Bundle.java": '''package android.os;
public class Bundle extends java.util.HashMap<String, String> {
 public void putString(String k, String v) { put(k,v); }
 public String getString(String k) { return get(k); }
}''',
    "android/content/Intent.java": '''package android.content;
public class Intent {
 public static final int FLAG_ACTIVITY_NEW_TASK=0x10000000, FLAG_ACTIVITY_CLEAR_TOP=0x04000000,
 FLAG_ACTIVITY_SINGLE_TOP=0x20000000;
 public Intent setClassName(String p,String c) { return this; }
 public Intent putExtra(String k,boolean v) { return this; }
 public Intent addFlags(int f) { return this; }
}''',
    "android/content/ActivityNotFoundException.java": '''package android.content;
public class ActivityNotFoundException extends RuntimeException {}''',
    "android/view/Gravity.java": '''package android.view;
public class Gravity { public static final int CENTER=17; }''',
    "android/widget/TextView.java": '''package android.widget;
public class TextView {
 public String text;
 public TextView(Object o) {}
 public void setText(String s) { text=s; }
 public void setGravity(int n) {}
 public void setPadding(int a,int b,int c,int d) {}
}''',
    "android/app/Activity.java": '''package android.app;
import android.os.Bundle;
import android.content.Intent;
public class Activity {
 public static int starts;
 public static boolean fail;
 public android.widget.TextView visible;
 protected void onCreate(Bundle state) {}
 protected void onSaveInstanceState(Bundle state) {}
 protected void onNewIntent(Intent intent) {}
 public void setIntent(Intent intent) {}
 public void startActivity(Intent intent) {
   starts++; if(fail) throw new android.content.ActivityNotFoundException();
 }
 public void finish() {}
 public void setContentView(android.widget.TextView v) { visible=v; }
}''',
    "HostChecks.java": '''import java.lang.reflect.Method;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import dev.herald.voicebridge.AssistActivity;
import dev.herald.voicebridge.tests.LaunchPolicy;
public class HostChecks {
 static void check(boolean ok,String msg) { if(!ok) throw new AssertionError(msg); }
 static void call(AssistActivity a,String name,Class<?> type,Object arg) throws Exception {
   Class<?> owner=a.getClass(); Method m=null;
   while(owner!=null) {
     try { m=owner.getDeclaredMethod(name,type); break; }
     catch(NoSuchMethodException missing) { owner=owner.getSuperclass(); }
   }
   if(m==null) throw new NoSuchMethodException(name);
   m.setAccessible(true); m.invoke(a,arg);
 }
 public static void main(String[] args) throws Exception {
   if(args[0].equals("guard")) {
     check(!LaunchPolicy.allows("dev.herald.voicebridge", "dev.herald.android",
       "dev.hermeskotlin.wear.MainActivity"), "Conflicting package/explicit Herald component MUST block");
     check(!LaunchPolicy.allows(null,"dev.herald.voicebridge","dev.herald.voicebridge.Unknown"),
       "Unknown bridge component MUST block");
     check(!LaunchPolicy.allows(null,null,null), "Unrestricted implicit MUST block");
     check(LaunchPolicy.allows("dev.herald.voicebridge",null,null), "Bridge implicit allowed");
     check(LaunchPolicy.allows(null,"dev.herald.voicebridge","dev.herald.voicebridge.AssistActivity"),
       "Exact bridge explicit allowed");
   } else {
     Activity.fail=true;
     AssistActivity first=new AssistActivity();
     call(first,"onCreate",Bundle.class,null);
     check(Activity.starts==1,"Initial attempt");
     String message=first.visible.text;
     Bundle saved=new Bundle();
     call(first,"onSaveInstanceState",Bundle.class,saved);
     Activity.fail=false;
     AssistActivity recreated=new AssistActivity();
     call(recreated,"onCreate",Bundle.class,saved);
     check(Activity.starts==1,"Recreation MUST NOT re-trigger Herald/microphone");
     check(recreated.visible!=null && message.equals(recreated.visible.text),"Preserve visible error");
     call(recreated,"onNewIntent",Intent.class,new Intent());
     check(Activity.starts==2,"Genuine new invocation retries exactly once");
     AssistActivity emptySaved=new AssistActivity();
     call(emptySaved,"onCreate",Bundle.class,new Bundle());
     check(Activity.starts==2,"Any saved state MUST NOT retry");
   }
   System.out.println("PASS: " + args[0]);
 }
}'''
}
