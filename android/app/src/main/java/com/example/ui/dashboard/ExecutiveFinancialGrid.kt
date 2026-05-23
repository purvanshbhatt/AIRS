package com.example.ui.dashboard

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AccountBalance
import androidx.compose.material.icons.rounded.AttachMoney
import androidx.compose.material.icons.rounded.Security
import androidx.compose.material.icons.rounded.TrendingUp
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.resilai.app.data.models.AssessmentSummary

data class FinancialMetric(
    val title: String,
    val value: String,
    val trend: String,
    val isPositive: Boolean,
    val icon: ImageVector
)

@Composable
fun ExecutiveFinancialGrid(
    modifier: Modifier = Modifier,
    isForensicMode: Boolean = false,
    summary: AssessmentSummary? = null
) {
    val metrics = listOf(
        FinancialMetric("Q3 Revenue", "$4.2M", "+12.5%", true, Icons.Rounded.AttachMoney),
        FinancialMetric("Operating Margin", "24.5%", "+2.1%", true, Icons.Rounded.TrendingUp),
        FinancialMetric("Risk Exposure", "$150k", "-5.4%", true, Icons.Rounded.Security),
        FinancialMetric("Capital Reserves", "$1.8M", "+1.2%", true, Icons.Rounded.AccountBalance)
    )

    Column(modifier = modifier.fillMaxWidth()) {
        Text(
            text = "Governance & Finance",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onBackground,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        // Trust Visualizer for GHI Score
        TrustVisualizer(
            ghiScore = (summary?.overallScore ?: 88.0).toInt(),
            isForensicMode = isForensicMode,
            summary = summary,
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 24.dp)
        )

        if (!isForensicMode) {
            Column(
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(16.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    FinancialMetricCard(metric = metrics[0], modifier = Modifier.weight(1f))
                    FinancialMetricCard(metric = metrics[1], modifier = Modifier.weight(1f))
                }
                Row(
                    horizontalArrangement = Arrangement.spacedBy(16.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    FinancialMetricCard(metric = metrics[2], modifier = Modifier.weight(1f))
                    FinancialMetricCard(metric = metrics[3], modifier = Modifier.weight(1f))
                }
            }
        }
    }
}

@Composable
fun FinancialMetricCard(metric: FinancialMetric, modifier: Modifier = Modifier) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        ),
        shape = RoundedCornerShape(16.dp),
        modifier = modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Icon(
                imageVector = metric.icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(28.dp)
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = metric.value,
                style = MaterialTheme.typography.headlineSmall,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = metric.title,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = metric.trend,
                style = MaterialTheme.typography.labelMedium,
                fontWeight = FontWeight.Bold,
                color = if (metric.isPositive) MaterialTheme.colorScheme.tertiary else MaterialTheme.colorScheme.error
            )
        }
    }
}

@Composable
fun TrustVisualizer(
    ghiScore: Int,
    isForensicMode: Boolean = false,
    summary: AssessmentSummary? = null,
    modifier: Modifier = Modifier
) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        shape = RoundedCornerShape(24.dp),
        modifier = modifier
    ) {
        if (isForensicMode) {
            Column(modifier = Modifier.padding(24.dp).fillMaxWidth()) {
                Text(
                    text = "Forensic Raw Logs",
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(16.dp))
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(MaterialTheme.colorScheme.background, RoundedCornerShape(8.dp))
                        .padding(16.dp)
                ) {
                    Text(
                        text = "{\n  \"timestamp\": \"2026-05-22T22:15:30Z\",\n  \"ghi_score\": ${ghiScore},\n  \"assessment_id\": \"${summary?.id}\",\n  \"tier\": \"${summary?.tier}\"\n}",
                        color = MaterialTheme.colorScheme.primary,
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = FontFamily.Monospace,
                        lineHeight = 18.sp
                    )
                }
            }
        } else {
            Row(
                modifier = Modifier
                    .padding(24.dp)
                    .fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "GHI Score",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        style = MaterialTheme.typography.labelLarge
                    )
                    Text(
                        text = "Governance Health Index",
                        color = MaterialTheme.colorScheme.onSurface,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "A measure of corporate trust and incident readiness.",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
                
                Spacer(modifier = Modifier.width(24.dp))

                Box(
                    modifier = Modifier.size(100.dp),
                    contentAlignment = Alignment.Center
                ) {
                    val circleColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.1f)
                    val progressColor = when {
                        ghiScore >= 80 -> MaterialTheme.colorScheme.tertiary
                        ghiScore >= 50 -> MaterialTheme.colorScheme.secondary
                        else -> MaterialTheme.colorScheme.error
                    }
                    
                    Canvas(modifier = Modifier.fillMaxSize()) {
                        drawArc(
                            color = circleColor,
                            startAngle = 135f,
                            sweepAngle = 270f,
                            useCenter = false,
                            style = Stroke(width = 12.dp.toPx(), cap = StrokeCap.Round)
                        )
                        drawArc(
                            color = progressColor,
                            startAngle = 135f,
                            sweepAngle = (ghiScore / 100f * 270f),
                            useCenter = false,
                            style = Stroke(width = 12.dp.toPx(), cap = StrokeCap.Round)
                        )
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = ghiScore.toString(),
                            fontSize = 32.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                    }
                }
            }
        }
    }
}
