package com.example.ui.findings

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.FilterList
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ui.dashboard.DashboardState
import com.example.ui.dashboard.DashboardViewModel
import com.example.ui.dashboard.PremiumFindingItem
import com.example.ui.theme.Cyan400
import com.example.ui.theme.Slate900
import com.example.ui.theme.TextSecondary

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FindingsScreen(viewModel: DashboardViewModel) {
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("FINDINGS_RELIABILITY", fontWeight = FontWeight.Black, color = Color.White, letterSpacing = 1.sp)
                        Text("ACTIVE THREAT TELEMETRY", style = MaterialTheme.typography.labelSmall, color = Cyan400)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Slate900),
                actions = {
                    IconButton(onClick = { /* Filter */ }) {
                        Icon(Icons.Rounded.FilterList, contentDescription = null, tint = Cyan400)
                    }
                }
            )
        },
        containerColor = Slate900
    ) { padding ->
        Column(modifier = Modifier.padding(padding).fillMaxSize().background(Slate900)) {
            // Search Bar
            OutlinedTextField(
                value = "",
                onValueChange = {},
                placeholder = { Text("Search deterministic findings...", color = TextSecondary) },
                leadingIcon = { Icon(Icons.Rounded.Search, contentDescription = null, tint = Cyan400) },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                shape = MaterialTheme.shapes.medium,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Cyan400,
                    unfocusedBorderColor = Color.White.copy(alpha = 0.1f),
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                ),
                singleLine = true
            )

            when (val currentState = state) {
                is DashboardState.Loading -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator(color = Cyan400)
                    }
                }
                is DashboardState.Success -> {
                    LazyColumn(
                        contentPadding = PaddingValues(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        items(currentState.findings) { finding ->
                            PremiumFindingItem(finding = finding)
                        }
                    }
                }
                is DashboardState.Error -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text("Failed to sync findings: ${currentState.message}", color = MaterialTheme.colorScheme.error)
                    }
                }
            }
        }
    }
}
