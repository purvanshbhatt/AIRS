package com.example.ui.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.FirebaseApp
import com.google.firebase.auth.FirebaseAuth
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await

sealed class LoginState {
    object Idle : LoginState()
    object Loading : LoginState()
    object Success : LoginState()
    data class Error(val message: String) : LoginState()
}

class LoginViewModel : ViewModel() {
    private val auth: FirebaseAuth? by lazy {
        try {
            // Check if Firebase is initialized before calling getInstance
            FirebaseApp.getInstance()
            FirebaseAuth.getInstance()
        } catch (e: Throwable) {
            android.util.Log.e("LoginViewModel", "Firebase Auth not available", e)
            null
        }
    }

    private val _state = MutableStateFlow<LoginState>(LoginState.Idle)
    val state: StateFlow<LoginState> = _state.asStateFlow()

    private val _email = MutableStateFlow("")
    val email: StateFlow<String> = _email.asStateFlow()

    private val _password = MutableStateFlow("")
    val password: StateFlow<String> = _password.asStateFlow()

    fun onEmailChange(newValue: String) {
        _email.value = newValue
    }

    fun onPasswordChange(newValue: String) {
        _password.value = newValue
    }

    fun login() {
        val emailValue = _email.value
        val passwordValue = _password.value

        if (emailValue.isBlank() || passwordValue.isBlank()) {
            _state.value = LoginState.Error("Email and password cannot be empty")
            return
        }

        viewModelScope.launch {
            _state.value = LoginState.Loading
            try {
                val firebaseAuth = auth
                if (firebaseAuth != null) {
                    firebaseAuth.signInWithEmailAndPassword(emailValue, passwordValue).await()
                    _state.value = LoginState.Success
                } else {
                    _state.value = LoginState.Error("Firebase not initialized. Check google-services.json.")
                }
            } catch (e: Exception) {
                _state.value = LoginState.Error(e.localizedMessage ?: "Login failed")
            }
        }
    }
}
