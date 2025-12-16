<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\CommentTrustController;
use App\Http\Controllers\GuestWebController;
use App\Http\Controllers\DashboardController;
use App\Http\Controllers\AdminAuthController;
use App\Http\Controllers\AdminController;
use App\Http\Controllers\UserManagementController;
use App\Http\Controllers\JobManagementController;

// ============================================================================
// Redirect root to appropriate page (login or dashboard)
// ============================================================================
Route::get('/', function () {
    if (auth()->check()) {
        // Check if user is admin
        if (auth()->user()->role > 0) {
            return redirect()->route('admin.dashboard');
        }
        // Regular/guest user
        return redirect()->route('dashboard');
    }
    return redirect()->route('login');
});

// ============================================================================
// Admin Authentication Pages (Public)
// ============================================================================
Route::prefix('/admin/auth')->group(function () {
    Route::get('/login', [AdminAuthController::class, 'showLoginForm'])->name('admin.auth.login');
    Route::post('/login', [AdminAuthController::class, 'login'])->name('admin.login');
});

// ============================================================================
// Guest Authentication Pages
// ============================================================================
Route::get('/login', [GuestWebController::class, 'showLoginForm'])->name('login');
Route::get('/register', [GuestWebController::class, 'showRegisterForm'])->name('register');
Route::post('/login', [GuestWebController::class, 'login'])->name('login.post');
Route::post('/register', [GuestWebController::class, 'register'])->name('register.post');
Route::post('/guest-login', [GuestWebController::class, 'guestLogin'])->name('guest.login');

// ============================================================================
// Protected Pages (Require Authentication)
// ============================================================================
Route::middleware('auth')->group(function () {
    Route::get('/dashboard', [DashboardController::class, 'index'])->name('dashboard');
    Route::post('/logout', [DashboardController::class, 'logout'])->name('logout');
    Route::get('/profile', [DashboardController::class, 'showProfile'])->name('profile');
    Route::put('/profile/update', [DashboardController::class, 'updateProfile'])->name('profile.update');
    Route::delete('/profile/delete', [DashboardController::class, 'deleteProfile'])->name('profile.delete');
    Route::get('/convert-to-user', [DashboardController::class, 'showConvertForm'])->name('convert-to-user');
    Route::post('/convert-to-user', [DashboardController::class, 'convertToUser'])->name('convert-to-user.post');
    
    // Guest-only API endpoints (for web interface token refresh)
    Route::post('/api/guest/refresh-token', [DashboardController::class, 'refreshGuestToken'])->name('guest.refresh-token');
});

// ============================================================================
// Admin Panel Routes (Require Authentication & Admin Role)
// ============================================================================
Route::middleware(['auth', 'admin'])->prefix('/admin')->group(function () {
    Route::get('/', [AdminController::class, 'dashboard'])->name('admin.dashboard');
    Route::post('/logout', [AdminAuthController::class, 'logout'])->name('admin.logout');

    // User Management
    Route::prefix('/users')->group(function () {
        Route::get('/', [UserManagementController::class, 'index'])->name('admin.users');
        Route::get('/{id}', [UserManagementController::class, 'show'])->name('admin.users.show');
        Route::delete('/{id}', [UserManagementController::class, 'destroy'])->name('admin.users.destroy');
        Route::post('/{id}/refresh-token', [UserManagementController::class, 'refreshToken'])->name('admin.users.refresh-token');
        Route::post('/{id}/extend-token', [UserManagementController::class, 'extendToken'])->name('admin.users.extend-token');
        Route::post('/{id}/reset-sessions', [UserManagementController::class, 'resetSessions'])->name('admin.users.reset-sessions');
    });

    // Job Management
    Route::prefix('/jobs')->group(function () {
        Route::get('/', [JobManagementController::class, 'index'])->name('admin.jobs');
    });

    // API Tester
    Route::get('/api-tester', [AdminController::class, 'apiTester'])->name('admin.api-tester');
});

// ============================================================================
// Legacy Routes
// ============================================================================
// Analysis page using DB data; mirrors Flask visualisasi.html
Route::get('/analysis/{productKey}', [CommentTrustController::class, 'analysisPage']);
