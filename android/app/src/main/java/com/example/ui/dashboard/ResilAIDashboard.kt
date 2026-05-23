package com.example.ui.dashboard

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.MenuBook
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Error
import androidx.compose.material.icons.rounded.Refresh
import androidx.compose.material.icons.rounded.Security
import androidx.compose.material.icons.rounded.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.resilai.app.data.models.AssessmentScore
import com.resilai.app.data.models.AssessmentSummary
import com.resilai.app.data.models.Finding
import com.example.ui.theme.Amber400
import com.example.ui.theme.Cyan400
import com.example.ui.theme.Emerald400
import com.example.ui.theme.Rose500
import com.example.ui.theme.Slate700
import com.example.ui.theme.Slate800

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResilAIDashboard(
    viewModel: DashboardViewModel = viewModel()
) {
    val state by viewModel.state.collectAsState()
    val isForensicMode by viewModel.isForensicMode.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("ResilAI", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onBackground) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                ),
                actions = {
                    IconButton(onClick = { viewModel.toggleMode() }) {
                        Icon(
                            if (isForensicMode) Icons.AutoMirrored.Rounded.MenuBook else Icons.Rounded.Security,
                            contentDescription = "Toggle Mode",
                            tint = Cyan400
                        )
                    }
                    IconButton(onClick = { viewModel.loadData() }) {
                        Icon(Icons.Rounded.Refresh, contentDescription = "Refresh", tint = Cyan400)
                    }
                }
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            when (val currentState = state) {
                is DashboardState.Loading -> {
                    CircularProgressIndicator(
                        modifier = Modifier.align(Alignment.Center),
                        color = Cyan400
                    )
                }
                is DashboardState.Error -> {
                    Column(
                        modifier = Modifier.align(Alignment.Center),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(Icons.Rounded.Error, contentDescription = null, tint = Rose500, modifier = Modifier.size(64.dp))
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("Error: ${currentState.message}", color = MaterialTheme.colorScheme.error)
                        Button(
                            onClick = { viewModel.loadData() },
                            colors = ButtonDefaults.buttonColors(containerColor = Cyan400),
                            modifier = Modifier.padding(top = 16.dp)
                        ) {
                            Text("Retry", color = MaterialTheme.colorScheme.onPrimary)
                        }
                    }
                }
                is DashboardState.Success -> {
                    DashboardContent(
                        summary = currentState.summary,
                        score = currentState.score,
                        isForensicMode = isForensicMode,
                        onToggleMode = viewModel::toggleMode
                    )
                }
            }
        }
    }
}

@Composable
fun DashboardContent(
    summary: AssessmentSummary,
    score: AssessmentScore,
    isForensicMode: Boolean,
    onToggleMode: () -> Unit
) {
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            HeaderSection(score)
        }
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                StatCard(
                    modifier = Modifier.weight(1f),
                    title = "Findings",
                    value = score.findingsCount.toString(),
                    icon = Icons.AutoMirrored.Rounded.MenuBook,
                    tint = Cyan400
                )
                StatCard(
                    modifier = Modifier.weight(1f),
                    title = "High Severity",
                    value = score.highSeverityCount.toString(),
                    icon = Icons.Rounded.Warning,
                    tint = Rose500
                )
            }
        }
        item {
            ExecutiveSummaryCard(summary.executiveSummaryText)
        }
        item {
            ExecutiveFinancialGrid(
                modifier = Modifier.padding(top = 8.dp),
                isForensicMode = isForensicMode,
                summary = summary
            )
        }
        item {
            Text(
                text = "Key Findings",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground,
                modifier = Modifier.padding(top = 8.dp, bottom = 4.dp)
            )
        }
        items(summary.findings) { finding ->
            FindingItem(finding = finding)
        }
    }
}

@Composable
fun HeaderSection(score: AssessmentScore) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Slate800),
        shape = RoundedCornerShape(24.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier
                .padding(24.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier.size(100.dp),
                contentAlignment = Alignment.Center
            ) {
                val circleColor = Slate700
                val progressColor = when {
                    score.overallScore >= 80 -> Emerald400
                    score.overallScore >= 50 -> Amber400
                    else -> Rose500
                }
                Canvas(modifier = Modifier.fillMaxSize()) {
                    drawArc(
                        color = circleColor,
                        startAngle = 0f,
                        sweepAngle = 360f,
                        useCenter = false,
                        style = Stroke(width = 8.dp.toPx(), cap = StrokeCap.Round)
                    )
                    drawArc(
                        color = progressColor,
                        startAngle = -90f,
                        sweepAngle = (score.overallScore / 100f * 360f).toFloat(),
                        useCenter = false,
                        style = Stroke(width = 8.dp.toPx(), cap = StrokeCap.Round)
                    )
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        text = score.overallScore.toInt().toString(),
                        fontSize = 32.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onBackground
                    )
                }
            }
            Spacer(modifier = Modifier.width(24.dp))
            Column {
                Text(
                    text = "Maturity Level",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.labelLarge
                )
                Text(
                    text = "${score.maturityLevel} - ${score.maturityName}",
                    color = MaterialTheme.colorScheme.onBackground,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(8.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Rounded.Security,
                        contentDescription = null,
                        tint = Emerald400,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "Deterministic Scoring",
                        color = Emerald400,
                        style = MaterialTheme.typography.labelSmall
                    )
                }
            }
        }
    }
}

@Composable
fun StatCard(
    modifier: Modifier = Modifier,
    title: String,
    value: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    tint: Color
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = Slate800),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Icon(imageVector = icon, contentDescription = null, tint = tint)
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = value,
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground
            )
            Text(
                text = title,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
fun ExecutiveSummaryCard(text: String?) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Slate800),
        shape = RoundedCornerShape(16.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "Executive Summary",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = Cyan400
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = text ?: "No summary available.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onBackground,
                lineHeight = 24.sp
            )
        }
    }
}

@Composable
fun FindingItem(finding: Finding) {
    val severityColor = when (finding.severity.uppercase()) {
        "CRITICAL" -> Rose500
        "HIGH" -> Rose500.copy(alpha = 0.8f)
        "MEDIUM" -> Amber400
        else -> Cyan400
    }
    
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Slate800)
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(12.dp)
                .clip(RoundedCornerShape(50))
                .background(severityColor)
        )
        Spacer(modifier = Modifier.width(16.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = finding.title,
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "${finding.severity} Severity",
                style = MaterialTheme.typography.labelMedium,
                color = severityColor
            )
        }
    }
}
