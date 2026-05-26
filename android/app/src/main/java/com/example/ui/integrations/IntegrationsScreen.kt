package com.example.ui.integrations

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.Key
import androidx.compose.material.icons.rounded.Webhook
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
import com.example.ui.theme.Cyan400
import com.example.ui.theme.Slate800
import com.example.ui.theme.Slate900
import com.example.ui.theme.TextSecondary
import com.resilai.app.data.models.ApiKeyMetadata
import com.resilai.app.data.models.Webhook

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun IntegrationsScreen(viewModel: DashboardViewModel) {
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("INTEGRATIONS_HUB", fontWeight = FontWeight.Black, color = Color.White, letterSpacing = 1.sp)
                        Text("EXTERNAL CONNECTORS", style = MaterialTheme.typography.labelSmall, color = Cyan400)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Slate900)
            )
        },
        containerColor = Slate900
    ) { padding ->
        Box(modifier = Modifier.padding(padding).fillMaxSize().background(Slate900)) {
            when (val currentState = state) {
                is DashboardState.Loading -> {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.Center), color = Cyan400)
                }
                is DashboardState.Error -> {
                    Text(
                        currentState.message,
                        color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.align(Alignment.Center)
                    )
                }
                is DashboardState.Success -> {
                    LazyColumn(
                        contentPadding = PaddingValues(16.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        item {
                            IntegrationHeader("API AUTHENTICATION KEYS", onAdd = {})
                        }
                        
                        if (currentState.apiKeys.isEmpty()) {
                            item {
                                EmptyStateCard("No active API keys found in this organization.")
                            }
                        } else {
                            items(currentState.apiKeys) { apiKey ->
                                PremiumApiKeyItem(apiKey)
                            }
                        }

                        item {
                            Spacer(Modifier.height(16.dp))
                            IntegrationHeader("DETERMINISTIC WEBHOOKS", onAdd = {})
                        }
                        
                        if (currentState.webhooks.isEmpty()) {
                            item {
                                EmptyStateCard("No operational webhooks configured.")
                            }
                        } else {
                            items(currentState.webhooks) { webhook ->
                                PremiumWebhookItem(webhook)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun IntegrationHeader(title: String, onAdd: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.labelMedium,
            color = Cyan400,
            fontWeight = FontWeight.Bold,
            letterSpacing = 1.2.sp
        )
        IconButton(onClick = onAdd) {
            Icon(Icons.Rounded.Add, contentDescription = null, tint = Cyan400)
        }
    }
}

@Composable
fun EmptyStateCard(text: String) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Slate800.copy(alpha = 0.3f)),
        shape = RoundedCornerShape(12.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.05f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Box(modifier = Modifier.padding(24.dp), contentAlignment = Alignment.Center) {
            Text(text, color = TextSecondary, style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
fun PremiumApiKeyItem(apiKey: ApiKeyMetadata) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Slate800.copy(alpha = 0.6f)),
        shape = RoundedCornerShape(16.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.1f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                color = Cyan400.copy(alpha = 0.1f),
                shape = RoundedCornerShape(8.dp)
            ) {
                Icon(
                    Icons.Rounded.Key, 
                    contentDescription = null, 
                    tint = Cyan400,
                    modifier = Modifier.padding(8.dp).size(20.dp)
                )
            }
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text(
                    text = "ID: ${apiKey.id.take(8)}...",
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Text(
                    text = "Prefix: ${apiKey.prefix} | Scopes: ${apiKey.scopes.joinToString(", ")}",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextSecondary
                )
            }
        }
    }
}

@Composable
fun PremiumWebhookItem(webhook: Webhook) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Slate800.copy(alpha = 0.6f)),
        shape = RoundedCornerShape(16.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color.White.copy(alpha = 0.1f)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                color = Cyan400.copy(alpha = 0.1f),
                shape = RoundedCornerShape(8.dp)
            ) {
                Icon(
                    Icons.Rounded.Webhook, 
                    contentDescription = null, 
                    tint = Cyan400,
                    modifier = Modifier.padding(8.dp).size(20.dp)
                )
            }
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text(
                    text = webhook.url,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                    maxLines = 1
                )
                Text(
                    text = "STATUS: OPERATIONAL | ID: ${webhook.id}",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextSecondary
                )
            }
        }
    }
}
