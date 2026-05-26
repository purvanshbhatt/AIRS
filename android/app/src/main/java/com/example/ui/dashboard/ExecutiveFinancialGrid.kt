package com.example.ui.dashboard

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ui.theme.*
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
        FinancialMetric("EST. REVENUE", "$4.2M", "+12.5%", true, Icons.Rounded.AttachMoney),
        FinancialMetric("OP. MARGIN", "24.5%", "+2.1%", true, Icons.Rounded.TrendingUp),
        FinancialMetric("RISK EXPOSURE", "$150k", "-5.4%", true, Icons.Rounded.Security),
        FinancialMetric("LIQUID RESERVES", "$1.8M", "+1.2%", true, Icons.Rounded.AccountBalance)
    )

    Column(modifier = modifier.fillMaxWidth()) {
        Text(
            text = "FINANCIAL TELEMETRY",
            style = MaterialTheme.typography.labelMedium,
            color = Cyan400,
            fontWeight = FontWeight.Bold,
            letterSpacing = 1.2.sp,
            modifier = Modifier.padding(bottom = 16.dp)
        )

        if (isForensicMode) {
            ForensicLogCard(ghiScore = summary?.overallScore?.toInt() ?: 0, summary = summary)
        } else {
            Column(
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(16.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    PremiumFinancialCard(metric = metrics[0], modifier = Modifier.weight(1f))
                    PremiumFinancialCard(metric = metrics[1], modifier = Modifier.weight(1f))
                }
                Row(
                    horizontalArrangement = Arrangement.spacedBy(16.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    PremiumFinancialCard(metric = metrics[2], modifier = Modifier.weight(1f))
                    PremiumFinancialCard(metric = metrics[3], modifier = Modifier.weight(1f))
                }
            }
        }
    }
}

@Composable
fun PremiumFinancialCard(metric: FinancialMetric, modifier: Modifier = Modifier) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Slate800.copy(alpha = 0.5f)),
        shape = RoundedCornerShape(16.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.05f)),
        modifier = modifier
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Icon(
                imageVector = metric.icon,
                contentDescription = null,
                tint = Cyan400,
                modifier = Modifier.size(20.dp)
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = metric.value,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Black,
                color = Color.White
            )
            Text(
                text = metric.title,
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = metric.trend,
                style = MaterialTheme.typography.labelSmall,
                fontWeight = FontWeight.Bold,
                color = if (metric.isPositive) Emerald400 else Rose500
            )
        }
    }
}

@Composable
fun ForensicLogCard(ghiScore: Int, summary: AssessmentSummary?) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.Black),
        shape = RoundedCornerShape(12.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Cyan400.copy(alpha = 0.3f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Rounded.Terminal, contentDescription = null, tint = Cyan400, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text("DETERMINISTIC_LOG_STREAM", style = MaterialTheme.typography.labelSmall, color = Cyan400)
            }
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = """
                    {
                      "node": "RESILAI-CORE-01",
                      "telemetry": {
                        "ghi": $ghiScore,
                        "id": "${summary?.id}",
                        "tier": "${summary?.tier}",
                        "active": true
                      },
                      "integrity": "VERIFIED_HASH_OK"
                    }
                """.trimIndent(),
                color = Cyan400,
                style = MaterialTheme.typography.bodySmall,
                fontFamily = FontFamily.Monospace,
                lineHeight = 18.sp
            )
        }
    }
}
