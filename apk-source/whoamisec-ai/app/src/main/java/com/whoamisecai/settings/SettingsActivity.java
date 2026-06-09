package com.whoamisecai.settings;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import com.whoamisecai.R;
import com.whoamisecai.utils.BiometricAuth;

/**
 * WHOAMISecAI SettingsActivity — API Key & Configuration
 */
public class SettingsActivity extends Activity {

    private static final String PREFS_NAME = "whoamisecai_prefs";
    private static final String KEY_ADMIN = "admin_key";
    private static final String KEY_MODEL = "selected_model";
    private static final String KEY_PIPELINE = "pipeline_mode";

    private SharedPreferences prefs;
    private EditText adminKeyInput, modelInput;
    private Spinner pipelineModeSpinner;
    private Button saveBtn, biometricBtn;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);

        prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        initViews();
        loadSettings();
    }

    private void initViews() {
        adminKeyInput = findViewById(R.id.settings_admin_key);
        modelInput = findViewById(R.id.settings_model);
        pipelineModeSpinner = findViewById(R.id.settings_pipeline_spinner);
        saveBtn = findViewById(R.id.settings_save);
        biometricBtn = findViewById(R.id.settings_biometric);
    }

    private void loadSettings() {
        adminKeyInput.setText(prefs.getString(KEY_ADMIN, "wsec_4ead532b0d0b02c7eab1791978d7d4ac"));
        modelInput.setText(prefs.getString(KEY_MODEL, "openai/gpt-4o"));

        String mode = prefs.getString(KEY_PIPELINE, "allm");
        String[] modeValues = getResources().getStringArray(R.array.pipeline_mode_values);
        for (int i = 0; i < modeValues.length; i++) {
            if (modeValues[i].equals(mode)) {
                pipelineModeSpinner.setSelection(i);
                break;
            }
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        // Refresh
        loadSettings();
    }
}
