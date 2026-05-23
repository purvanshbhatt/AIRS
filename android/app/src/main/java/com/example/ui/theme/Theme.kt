package com.example.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

private val ModernDarkColorScheme =
  darkColorScheme(
    primary = Cyan400,
    secondary = Amber400,
    tertiary = Emerald400,
    background = Slate900,
    surface = Slate800,
    onPrimary = Slate900,
    onSecondary = Slate900,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
    surfaceVariant = Slate700,
    onSurfaceVariant = TextSecondary,
    error = Rose500
  )

private val ModernLightColorScheme =
  lightColorScheme(
    primary = Cyan500,
    secondary = Amber400,
    tertiary = Emerald400,
    background = Color.White,
    surface = Slate700.copy(alpha = 0.05f),
    onPrimary = Color.White,
    onSecondary = Slate900,
    onBackground = Slate900,
    onSurface = Slate900,
    surfaceVariant = Slate700.copy(alpha = 0.1f),
    onSurfaceVariant = Slate700,
    error = Rose500
  )

@Composable
fun MyApplicationTheme(
  darkTheme: Boolean = isSystemInDarkTheme(),
  dynamicColor: Boolean = false,
  content: @Composable () -> Unit,
) {
  val colorScheme = if (darkTheme) ModernDarkColorScheme else ModernLightColorScheme

  MaterialTheme(colorScheme = colorScheme, typography = Typography, content = content)
}
