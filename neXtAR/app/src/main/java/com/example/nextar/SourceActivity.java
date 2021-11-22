package com.example.nextar;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;

public class SourceActivity extends AppCompatActivity {

    //if online button is pressed
    //Button onlineSourceButton = (Button)findViewById(R.id.sourceOnlineButton);

    //if phone file button is pressed
    //Button phoneSourceButton = (Button)findViewById(R.id.sourcePhoneFilesButton);

    //if computer files button is pressed
    //Button computerSourceButton = (Button)findViewById(R.id.sourceComputerButton);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_source);

    }

    //if online button is pressed, user is sent to OnlineSourceActivity
    public void sourceOnlineButtonPressed(View view) {
        Intent intent = new Intent(SourceActivity.this, OnlineSourceActivity.class);
        startActivity(intent);
    }

    //if phone file button is pressed, user is sent to PhoneFileSourceActivity
    public void sourcePhoneFileButtonPressed(View view) {
        Intent intent = new Intent(SourceActivity.this, PhoneFileSourceActivity.class);
        startActivity(intent);
    }

    //if computer button is pressed, user is sent to ComputerSourceActivity
    public void sourceComputerButtonPressed(View view) {
        Intent intent = new Intent(SourceActivity.this, ComputerSourceActivity.class);
        startActivity(intent);
    }

    public void testArucoButtonPressed(View view){
        Intent intent = new Intent(SourceActivity.this, TestArucoActivity.class);
        startActivity(intent);
    }
}