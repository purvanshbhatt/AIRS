package com.example.ui.dashboard

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ui.theme.*

@Composable
fun GovernanceHealthGauge(
    score: Float,
    status: String,
    modifier: Modifier = Modifier
) {
    val animatedScore = remember { Animatable(0f) }
    LaunchedEffect(score) {
        animatedScore.animateTo(
            targetValue = score.coerceIn(0f, 100f),
            animationSpec = tween(durationMillis = 1500)
        )
    }

    Card(
        colors = CardDefaults.cardColors(
            containerColor = Slate800.copy(alpha = 0.4f)
        ),
        shape = RoundedCornerShape(24.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.1f)),
        modifier = modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(24.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "TRUST_VISUALIZER",
                    color = Cyan400,
                    style = MaterialTheme.typography.labelSmall,
                    letterSpacing = 1.5.sp
                )
                Text(
                    text = "Governance Health Index",
                    color = Color.White,
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.ExtraBold
                )
                
                Spacer(modifier = Modifier.height(16.dp))

                BackendStatus(status = status)
            }

            Box(
                modifier = Modifier.size(140.dp),
                contentAlignment = Alignment.Center
            ) {
                val circleTrackColor = Color.White.copy(alpha = 0.05f)
                val progressColor = when {
                    score >= 80f -> Emerald400
                    score >= 50f -> Amber400
                    else -> Rose500
                }

                // Glow Effect
                Box(
                    modifier = Modifier
                        .size(100.dp)
                        .blur(30.dp)
                        .background(progressColor.copy(alpha = 0.15f), RoundedCornerShape(50))
                )

                Canvas(modifier = Modifier.fillMaxSize()) {
                    drawArc(
                        color = circleTrackColor,
                        startAngle = 135f,
                        sweepAngle = 270f,
                        useCenter = false,
                        style = Stroke(width = 14.dp.toPx(), cap = StrokeCap.Round)
                    )
                    drawArc(
                        brush = Brush.sweepGradient(
                            0f to progressColor.copy(alpha = 0.5f),
                            0.5f to progressColor,
                            1f to progressColor
                        ),
                        startAngle = 135f,
                        sweepAngle = (animatedScore.value / 100f * 270f),
                        useCenter = false,
                        style = Stroke(width = 14.dp.toPx(), cap = StrokeCap.Round)
                    )
                }

                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = animatedScore.value.toInt().toString(),
                        fontSize = 42.sp,
                        fontWeight = FontWeight.Black,
                        color = Color.White
                    )
                    Text(
                        text = "GHI",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = Cyan400,
                        letterSpacing = 1.sp
                    )
                }
            }
        }
    }
}

