package com.example.ui.dashboard

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.Logout
import androidx.compose.material.icons.automirrored.rounded.MenuBook
import androidx.compose.material.icons.rounded.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.ui.theme.*
import com.resilai.app.data.models.AssessmentScore
import com.resilai.app.data.models.AssessmentSummary
import com.resilai.app.data.models.Finding

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResilAIDashboard(
    viewModel: DashboardViewModel = viewModel()
) {
    val state by viewModel.state.collectAsState()
    val isForensicMode by viewModel.isForensicMode.collectAsState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Slate900)
    ) {
        Scaffold(
            topBar = {
                CenterAlignedTopAppBar(
                    title = {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                "RESILAI",
                                fontWeight = FontWeight.ExtraBold,
                                color = Color.White,
                                letterSpacing = 2.sp
                            )
                            Text(
                                "COMMAND CENTER",
                                style = MaterialTheme.typography.labelSmall,
                                color = Cyan400,
                                letterSpacing = 1.sp
                            )
                        }
                    },
                    colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                        containerColor = Color.Transparent,
                        titleContentColor = Color.White
                    ),
                    actions = {
                        IconButton(onClick = { viewModel.toggleMode() }) {
                            Icon(
                                if (isForensicMode) Icons.Rounded.Code else Icons.Rounded.Shield,
                                contentDescription = "Toggle Mode",
                                tint = Cyan400
                            )
                        }
                        IconButton(onClick = { viewModel.loadData() }) {
                            Icon(Icons.Rounded.Refresh, contentDescription = "Refresh", tint = Cyan400)
                        }
                        IconButton(onClick = {
                            com.google.firebase.auth.FirebaseAuth.getInstance().signOut()
                            com.example.api.AuthEventManager.emitUnauthorized()
                        }) {
                            Icon(Icons.AutoMirrored.Rounded.Logout, contentDescription = "Logout", tint = Rose500)
                        }
                    }
                )
            },
            containerColor = Color.Transparent
        ) { padding ->
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
            ) {
                when (val currentState = state) {
                    is DashboardState.Loading -> {
                        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            CircularProgressIndicator(color = Cyan400)
                        }
                    }
                    is DashboardState.Error -> {
                        Column(
                            modifier = Modifier.align(Alignment.Center),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Icon(
                                if (currentState.isBackendDown) Icons.Rounded.CloudOff else Icons.Rounded.Error,
                                contentDescription = null,
                                tint = Rose500,
                                modifier = Modifier.size(64.dp)
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                if (currentState.isBackendDown) "BACKEND OFFLINE" else "ERROR DETECTED",
                                fontWeight = FontWeight.Bold,
                                color = Color.White,
                                style = MaterialTheme.typography.headlineSmall
                            )
                            Text(
                                currentState.message,
                                color = TextSecondary,
                                modifier = Modifier.padding(16.dp),
                                textAlign = androidx.compose.ui.text.style.TextAlign.Center
                            )
                            Button(
                                onClick = { viewModel.loadData() },
                                colors = ButtonDefaults.buttonColors(containerColor = BrandPrimary),
                                shape = RoundedCornerShape(8.dp)
                            ) {
                                Text("RETRY CONNECTION", color = Color.White, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                    is DashboardState.Success -> {
                        DashboardContent(
                            summary = currentState.summary,
                            score = currentState.score,
                            isForensicMode = isForensicMode
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun DashboardContent(
    summary: AssessmentSummary,
    score: AssessmentScore,
    isForensicMode: Boolean
) {
    LazyVerticalGrid(
        columns = GridCells.Adaptive(minSize = 340.dp),
        contentPadding = PaddingValues(16.dp),
        horizontalArrangement = Arrangement.spacedBy(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item(span = { androidx.compose.foundation.lazy.grid.GridItemSpan(maxLineSpan) }) {
            GovernanceHealthGauge(
                score = score.overallScore.toFloat(),
                status = if (score.overallScore >= 80) "SOC_VERIFIED" else "PROVISIONAL",
                modifier = Modifier.fillMaxWidth()
            )
        }

        item {
            ExecutiveFinancialGrid(
                isForensicMode = isForensicMode,
                summary = summary
            )
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Text(
                    "CORE TELEMETRY",
                    style = MaterialTheme.typography.labelMedium,
                    color = Cyan400,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.2.sp
                )
                Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    PremiumStatCard(
                        modifier = Modifier.weight(1f),
                        title = "TOTAL FINDINGS",
                        value = score.findingsCount.toString(),
                        icon = Icons.Rounded.Analytics,
                        color = Cyan400
                    )
                    PremiumStatCard(
                        modifier = Modifier.weight(1f),
                        title = "HIGH RISK",
                        value = score.highSeverityCount.toString(),
                        icon = Icons.Rounded.ReportProblem,
                        color = Rose500
                    )
                }
                
                ExecutiveSummaryCard(summary.executiveSummaryText)
            }
        }

        item(span = { androidx.compose.foundation.lazy.grid.GridItemSpan(maxLineSpan) }) {
            Text(
                "CRITICAL GOVERNANCE FINDINGS",
                style = MaterialTheme.typography.labelMedium,
                color = Cyan400,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.2.sp,
                modifier = Modifier.padding(top = 8.dp)
            )
        }

        items(summary.findings) { finding ->
            PremiumFindingItem(finding = finding)
        }
    }
}

@Composable
fun PremiumStatCard(
    modifier: Modifier = Modifier,
    title: String,
    value: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    color: Color
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = Slate800.copy(alpha = 0.6f)),
        shape = RoundedCornerShape(16.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, color.copy(alpha = 0.2f))
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(icon, contentDescription = null, tint = color, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text(title, style = MaterialTheme.typography.labelSmall, color = TextSecondary)
            }
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                value,
                style = MaterialTheme.typography.headlineLarge,
                fontWeight = FontWeight.Black,
                color = Color.White
            )
        }
    }
}

@Composable
fun PremiumFindingItem(finding: Finding) {
    val color = when (finding.severity.uppercase()) {
        "CRITICAL" -> Rose500
        "HIGH" -> Orange400
        "MEDIUM" -> Amber400
        else -> Cyan400
    }

    Card(
        colors = CardDefaults.cardColors(containerColor = Slate800.copy(alpha = 0.6f)),
        shape = RoundedCornerShape(12.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, color.copy(alpha = 0.15f))
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .clip(RoundedCornerShape(50))
                    .background(color)
            )
            Spacer(modifier = Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    finding.title,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Text(
                    finding.severity,
                    style = MaterialTheme.typography.labelSmall,
                    color = color,
                    fontWeight = FontWeight.Bold
                )
            }
            Icon(Icons.Rounded.ChevronRight, contentDescription = null, tint = TextSecondary)
        }
    }
}

@Composable
fun ExecutiveSummaryCard(text: String?) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Slate800.copy(alpha = 0.4f)),
        shape = RoundedCornerShape(16.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.05f))
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("EXECUTIVE OVERVIEW", style = MaterialTheme.typography.labelSmall, color = Cyan400)
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text ?: "Analyzing governance telemetry...",
                style = MaterialTheme.typography.bodyMedium,
                color = TextPrimary,
                lineHeight = 22.sp
            )
        }
    }
}
