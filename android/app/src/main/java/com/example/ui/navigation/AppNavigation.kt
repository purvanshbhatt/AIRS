package com.example.ui.navigation

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.MenuBook
import androidx.compose.material.icons.rounded.Dashboard
import androidx.compose.material.icons.rounded.IntegrationInstructions
import androidx.compose.material.icons.rounded.Security
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.ui.theme.*
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
    val dashboardViewModel: DashboardViewModel = viewModel()
    
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = navBackStackEntry?.destination

    // Check for existing session on start
    val currentUser = remember { com.google.firebase.auth.FirebaseAuth.getInstance().currentUser }
    val startRoute = if (currentUser != null) Screen.Dashboard.route else Screen.Login.route

    LaunchedEffect(Unit) {
        if (currentUser != null) {
            dashboardViewModel.loadData()
        }

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
                    containerColor = Slate900,
                    tonalElevation = 0.dp,
                    modifier = Modifier.background(Slate900)
                ) {
                    items.forEach { screen ->
                        NavigationBarItem(
                            icon = { Icon(screen.icon, contentDescription = null) },
                            label = { 
                                Text(
                                    screen.title.uppercase(), 
                                    style = MaterialTheme.typography.labelSmall,
                                    fontWeight = FontWeight.Bold,
                                    letterSpacing = 1.sp
                                ) 
                            },
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
                                selectedIconColor = Cyan400,
                                selectedTextColor = Cyan400,
                                unselectedIconColor = TextSecondary,
                                unselectedTextColor = TextSecondary,
                                indicatorColor = Slate800
                            )
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(
            navController = navController,
            startDestination = startRoute,
            modifier = Modifier.padding(innerPadding)
        ) {
            composable(Screen.Login.route) {
                LoginScreen(onLoginSuccess = {
                    dashboardViewModel.loadData()
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
