package com.example.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.MenuBook
import androidx.compose.material.icons.rounded.Dashboard
import androidx.compose.material.icons.rounded.IntegrationInstructions
import androidx.compose.material.icons.rounded.Security
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.example.ui.dashboard.DashboardViewModel
import com.example.ui.dashboard.ResilAIDashboard
import com.example.ui.login.LoginScreen
import com.example.ui.findings.FindingsScreen
import com.example.ui.integrations.IntegrationsScreen
import com.example.api.AuthEventManager

sealed class Screen(val route: String, val title: String, val icon: androidx.compose.ui.graphics.vector.ImageVector) {
    object Login : Screen("login", "Login", Icons.Rounded.Security)
    object Dashboard : Screen("dashboard", "Dashboard", Icons.Rounded.Dashboard)
    object Findings : Screen("findings", "Findings", Icons.AutoMirrored.Rounded.MenuBook)
    object Integrations : Screen("integrations", "Integrations", Icons.Rounded.IntegrationInstructions)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    // Shared ViewModel for simplicity in this demo. 
    // In a production app, each screen might have its own ViewModel 
    // or share a Hilt/Dagger scoped ViewModel.
    val dashboardViewModel: DashboardViewModel = viewModel()
    
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = navBackStackEntry?.destination

    LaunchedEffect(Unit) {
        AuthEventManager.unauthorizedEvents.collect {
            if (currentDestination?.route != Screen.Login.route) {
                navController.navigate(Screen.Login.route) {
                    popUpTo(0) { inclusive = true }
                    launchSingleTop = true
                }
            }
        }
    }
    
    val items = listOf(
        Screen.Dashboard,
        Screen.Findings,
        Screen.Integrations
    )
    
    val showBottomBar = currentDestination?.route != Screen.Login.route

    Scaffold(
        bottomBar = {
            if (showBottomBar) {
                NavigationBar(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant,
                ) {
                    items.forEach { screen ->
                        NavigationBarItem(
                            icon = { Icon(screen.icon, contentDescription = null) },
                            label = { Text(screen.title) },
                            selected = currentDestination?.hierarchy?.any { it.route == screen.route } == true,
                            onClick = {
                                navController.navigate(screen.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = MaterialTheme.colorScheme.primary,
                                selectedTextColor = MaterialTheme.colorScheme.primary,
                                unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                indicatorColor = MaterialTheme.colorScheme.surfaceVariant
                            )
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = Screen.Login.route,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Screen.Login.route) {
                LoginScreen(onLoginSuccess = {
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                })
            }
            composable(Screen.Dashboard.route) {
                ResilAIDashboard(viewModel = dashboardViewModel)
            }
            composable(Screen.Findings.route) {
                FindingsScreen(viewModel = dashboardViewModel)
            }
            composable(Screen.Integrations.route) {
                IntegrationsScreen(viewModel = dashboardViewModel)
            }
        }
    }
}
