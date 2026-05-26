package com.example

import android.app.Application
import com.google.firebase.FirebaseApp

class ResilAIApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        try {
            if (FirebaseApp.getApps(this).isEmpty()) {
                FirebaseApp.initializeApp(this)
                android.util.Log.d("ResilAI", "Firebase initialized successfully")
            } else {
                android.util.Log.d("ResilAI", "Firebase already initialized")
            }
        } catch (e: Exception) {
            android.util.Log.e("ResilAI", "Firebase initialization failed", e)
        }
    }
}
