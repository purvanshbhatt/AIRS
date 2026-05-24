package com.example.ui.dashboard

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ui.theme.Amber400
import com.example.ui.theme.Emerald400
import com.example.ui.theme.Rose500
import com.example.ui.theme.Slate750 // high contrast accessibility fallback if needed

@Composable
fun GovernanceHealthGauge(
    score: Float,
    status: String,
    modifier: Modifier = Modifier
) {
    // Animatable to animate progress on initial load
    val animatedScore = remember { Animatable(0f) }
    LaunchedEffect(score) {
        animatedScore.animateTo(
            targetValue = score.coerceIn(0f, 100f),
            animationSpec = tween(durationMillis = 1000)
        )
    }

    // Using FilledCard styling with tonal elevation (M3 Surface Tones)
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        ),
        shape = RoundedCornerShape(24.dp),
        modifier = modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Governance Health Index",
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            
            Spacer(modifier = Modifier.height(16.dp))

            Box(
                modifier = Modifier.size(120.dp),
                contentAlignment = Alignment.Center
            ) {
                val circleTrackColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.1f)
                val progressColor = when {
                    score >= 80f -> Emerald400
                    score >= 50f -> Amber400
                    else -> Rose500
                }

                Canvas(modifier = Modifier.fillMaxSize()) {
                    // Full track arc for high accessibility contrast
                    drawArc(
                        color = circleTrackColor,
                        startAngle = 135f,
                        sweepAngle = 270f,
                        useCenter = false,
                        style = Stroke(width = 12.dp.toPx(), cap = StrokeCap.Round)
                    )
                    // Animated score progress arc
                    drawArc(
                        color = progressColor,
                        startAngle = 135f,
                        sweepAngle = (animatedScore.value / 100f * 270f),
                        useCenter = false,
                        style = Stroke(width = 12.dp.toPx(), cap = StrokeCap.Round)
                    )
                }

                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = animatedScore.value.toInt().toString(),
                        fontSize = 32.sp,
                        fontWeight = FontWeight.ExtraBold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    Text(
                        text = "GHI",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            VerificationBadge(status = status)
        }
    }
}

@Composable
fun VerificationBadge(status: String) {
    val (backgroundColor, textColor, textLabel) = when (status) {
        "SOC_VERIFIED" -> Triple(
            Emerald400.copy(alpha = 0.15f),
            Emerald400,
            "SOC VERIFIED"
        )
        "PROVISIONAL" -> Triple(
            Amber400.copy(alpha = 0.15f),
            Amber400,
            "PROVISIONAL"
        )
        else -> Triple(
            MaterialTheme.colorScheme.errorContainer,
            MaterialTheme.colorScheme.onErrorContainer,
            status.uppercase()
        )
    }

    Surface(
        color = backgroundColor,
        contentColor = textColor,
        shape = RoundedCornerShape(8.dp),
        border = CardDefaults.outlinedCardBorder().copy(
            brush = androidx.compose.ui.graphics.SolidColor(textColor.copy(alpha = 0.3f))
        )
    ) {
        Text(
            text = textLabel,
            modifier = Modifier.padding(horizontal = 12.dp, py = 6.dp),
            style = MaterialTheme.typography.labelMedium,
            fontWeight = FontWeight.Bold,
            letterSpacing = 1.2.sp
        )
    }
}
