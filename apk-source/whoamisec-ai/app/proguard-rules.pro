# WHOAMISecAI ProGuard Rules
-keepattributes *Annotation*
-keepattributes SourceFile,LineNumberTable
-keepattributes Signature
-keep class com.whoamisecai.** { *; }
-keepclassmembers class com.whoamisecai.** { *; }
-dontwarn com.whoamisecai.utils.**
-keep class androidx.recyclerview.widget.** { *; }
