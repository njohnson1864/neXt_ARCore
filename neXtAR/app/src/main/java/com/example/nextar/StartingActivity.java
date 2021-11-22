package com.example.nextar;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;

public class StartingActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_starting);

        //switches to source activity after 3 seconds
        final Handler handler = new Handler();
        handler.postDelayed(new Runnable() {
            public void run() {
                Intent mInHome = new Intent(StartingActivity.this, SourceActivity.class);
                StartingActivity.this.startActivity(mInHome);
                StartingActivity.this.finish();
            }
        }, 3000);
    }
}
