# JARVIS ProGuard Rules
# Keep project classes
-keep class com.whoamisecai.jarvis.** { *; }

# Keep OkHttp
-keep class okhttp3.** { *; }
-keep interface okhttp3.** { *; }
-dontwarn okhttp3.**
-dontwarn okio.**

# Keep JSON classes
-keep class org.json.** { *; }
-keep class com.google.gson.** { *; }

# Keep SpeechRecognizer related
-keep class android.speech.** { *; }

# Keep TTS related
-keep class android.speech.tts.** { *; }

# Keep AudioRecord related
-keep class android.media.AudioRecord { *; }

# Keep enum values
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

# Remove logging in release
-assumenosideeffects class android.util.Log {
    public static *** d(...);
    public static *** v(...);
    public static *** i(...);
}
