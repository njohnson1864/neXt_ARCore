package com.example.nextar;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebView;
import android.widget.EditText;

public class OnlineSourceActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_online_source);
    }
    //When "select URL source" button is pressed, figure out which string should be passed, then send the user to AR activity
    public void selectURLSourceButtonPressed(View view) {
        //get length of strings to decide which to pass to next activity
        //int ghStringLength = ghSendText.getText().length();
        //int odStringLength = odSendText.getText().length();
        EditText ghSendText;
        ghSendText = (EditText)findViewById(R.id.editText);
        String ghString = ghSendText.getText().toString();
        //String odString = odSendText.getText().toString();

        // if github url is longer than onedrive url, this indicates the user has copied and pasted into the editText field
        // if this is the case, copy the string value and send that string to the AR activity to be used in loading the model at runtime
        //if (ghStringLength > odStringLength) {
            Intent sendGHStringIntent = new Intent(OnlineSourceActivity.this, ARActivity.class);
            sendGHStringIntent.putExtra("ghString", ghString);
            startActivity(sendGHStringIntent);
        //}
        //The same for the case of the onedrive Edit Text being longer than the github editText. This is not a good code practice for the long run
        //but it will do for now......
        /*if (odStringLength > ghStringLength) {
            Intent sendODStringIntent = new Intent(OnlineSourceActivity.this, ARActivity.class);
            sendODStringIntent.putExtra("odString", odString);
            startActivity(sendODStringIntent);
        }*/

        //Send user to AR activity
        Intent intent = new Intent(OnlineSourceActivity.this, ARActivity.class);
        startActivity(intent);
    }

    //When GitHub button is pressed, open url to that site for sign-in
    public void githubButtonPressed (View view) {
        Intent githubBrowserIntent = new Intent(Intent.ACTION_VIEW, Uri.parse("http://www.github.com"));
        startActivity(githubBrowserIntent);
        //MUST  USE PERMALINK ON GITHUB TO COPY FULL PATH URL
    }

    //When onedrive button is pressed, open url to that site for sign-in
    public void oneDriveButtonPressed (View view) {
        Intent oneDriveButtonPressed = new Intent(Intent.ACTION_VIEW, Uri.parse("http://www.onedrive.live.com/about/en-us/signin/"));
        startActivity(oneDriveButtonPressed);
    }
}