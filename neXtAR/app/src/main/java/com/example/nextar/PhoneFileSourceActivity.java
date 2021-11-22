package com.example.nextar;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Environment;
import android.util.Log;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.ListView;
import java.io.File;
import java.util.ArrayList;
import java.util.List;


public class PhoneFileSourceActivity extends AppCompatActivity {
    EditText modelNameEditText;
    ListView listOfGLBFiles;

    // Storage Permissions
    private static final int REQUEST_EXTERNAL_STORAGE = 1;
    private static final String[] PERMISSIONS_STORAGE = {
            Manifest.permission.READ_EXTERNAL_STORAGE,
            Manifest.permission.WRITE_EXTERNAL_STORAGE
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_phone_file_source);
        verifyStoragePermissions();
        modelNameEditText = (EditText) findViewById(R.id.modelNameEditText);
        listOfGLBFiles = (ListView) findViewById(R.id.list);

        String path = Environment.getExternalStorageDirectory().toString() + "/Download/";
        Log.d("Files", "Path: " + path);
        File directory = new File(path);
        File[] files = directory.listFiles();
        Log.d("Files", "Size: "+ files.length);
        List<String> fileArrayList = new ArrayList<String>();
        ArrayAdapter<String> arrayAdapter = new ArrayAdapter<String>(
                this,
                android.R.layout.simple_list_item_1,
                fileArrayList
        );

        //Parses folder and returns all files in the folder to the LOGCAT
        for (int i = 0; i < files.length; i++)
        {
            String fileNameToAdd = files[i].getName();
            Log.d("Files", "FileName:" + fileNameToAdd);

            //Adds .glb files only to the array list shown in the ListView
            if (fileNameToAdd.endsWith(".glb")){
                fileArrayList.add(fileNameToAdd);
                listOfGLBFiles.setAdapter(arrayAdapter);
            }
        }

        //set onclick listener to return the selected file's name to the editText
        listOfGLBFiles.setOnItemClickListener(new AdapterView.OnItemClickListener() {
            public void onItemClick(AdapterView<?> arg0, View arg1, int arg2, long arg3) {
                String dataModelName = (String)arg0.getItemAtPosition(arg2);
                modelNameEditText.setText(dataModelName);
            }
        });
    }

    public void beginARActivityButtonPressed(View view) {
        //on button press, start AR activity
        Intent intent = new Intent(PhoneFileSourceActivity.this, ARActivity.class);
        startActivity(intent);

        //Completing full path for model
        String rootDir = Environment.getExternalStorageDirectory().toString();
        String modelName = modelNameEditText.getText().toString();
        //String modelDirectory = rootDir + modelName;
        String modelDirectory = rootDir;
        String modelFileName = modelName;


        //Sends modelDirectory as an Extra to the AR activity
        //Intent sendPhoneSourcePathIntent = new Intent(PhoneFileSourceActivity.this, ARActivity.class);
        //sendPhoneSourcePathIntent.putExtra("modelDirectory",modelDirectory);
        //sendPhoneSourcePathIntent.putExtra("modelDirectory",modelDirectory);
        //startActivity(sendPhoneSourcePathIntent);

        Intent sendPhoneSourcePathIntent = new Intent(PhoneFileSourceActivity.this, ARActivity.class);
        Bundle extras = new Bundle();
        extras.putString("modelDirectory",modelDirectory);
        extras.putString("modelFileName", modelFileName);
        sendPhoneSourcePathIntent.putExtras(extras);
        startActivity(sendPhoneSourcePathIntent);
    }

    public void verifyStoragePermissions() {
        // Check if we have write permission
        int permission = ActivityCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE);

        if (permission != PackageManager.PERMISSION_GRANTED) {
            // We don't have permission so prompt the user
            ActivityCompat.requestPermissions(
                    this,
                    PERMISSIONS_STORAGE,
                    REQUEST_EXTERNAL_STORAGE
            );
        }
    }
}

