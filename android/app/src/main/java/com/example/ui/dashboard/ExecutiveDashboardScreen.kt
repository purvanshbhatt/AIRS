package com.example.ui.dashboard

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.resilai.app.data.models.AssessmentSummary

@Composable
fun ExecutiveDashboardScreen(
    summary: AssessmentSummary?,
    telemetryActive: Boolean,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Color(0xFF0F141A))
            .padding(16.dp)
    ) {
        if (telemetryActive) {
            Surface(
                modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp),
                color = Color(0xFF14532D), // Dark emerald for SOC verified
                shape = RoundedCornerShape(8.dp)
            ) {
                Text(
                    text = "SOC VERIFIED TELEMETRY ACTIVE",
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(12.dp),
                    style = MaterialTheme.typography.labelMedium
                )
            }
        }

        Text(
            text = "Governance Health Index (GHI)",
            color = Color(0xFFDFE2EB),
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 24.dp)
        )

        val score = summary?.overall_score ?: 0.0

        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(300.dp),
            contentAlignment = Alignment.Center
        ) {
            Canvas(modifier = Modifier.size(250.dp)) {
                drawArc(
                    color = Color(0xFF31353C),
                    startAngle = 135f,
                    sweepAngle = 270f,
                    useCenter = false,
                    style = Stroke(width = 30f, cap = StrokeCap.Round)
                )

                val sweep = (score / 100f) * 270f
                val progressColor = when {
                    score < 50 -> Color(0xFFFFB4AB)
                    score < 80 -> Color(0xFFFFD97D)
                    else -> Color(0xFFA1C9FF)
                }

                drawArc(
                    color = progressColor,
                    startAngle = 135f,
                    sweepAngle = sweep.toFloat(),
                    useCenter = false,
                    style = Stroke(width = 30f, cap = StrokeCap.Round)
                )
            }

            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "${score.toInt()}",
                    color = Color.White,
                    fontSize = 56.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "GHI SCORE",
                    color = Color(0xFFBFC7D5),
                    fontSize = 14.sp
                )
            }
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        
        // Executive Financial Grid Concept
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF1C2026)),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "Executive Summary",
                    color = Color(0xFFDFE2EB),
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(bottom = 8.dp)
                )
                Text(
                    text = summary?.executive_summary ?: "Awaiting data...",
                    color = Color(0xFFBFC7D5),
                    fontSize = 14.sp,
                    lineHeight = 20.sp
                )
            }
        }
    }
}
