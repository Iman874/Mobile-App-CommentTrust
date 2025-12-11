<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\GuestWebController;
use App\Http\Controllers\DashboardController;

Route::middleware('web')->group(function () {
    // Redirect root to login or dashboard
    Route::get('/', function () {
        if (auth()->check()) {
            return redirect('/dashboard');
        }
        return redirect('/login');
    });

    // Guest web pages (no auth required)
    Route::get('/login', [GuestWebController::class, 'showLoginForm'])->name('login');
    Route::get('/register', [GuestWebController::class, 'showRegisterForm'])->name('register');
    Route::post('/login', [GuestWebController::class, 'login'])->name('login.post');
    Route::post('/register', [GuestWebController::class, 'register'])->name('register.post');
    Route::post('/guest-login', [GuestWebController::class, 'guestLogin'])->name('guest.login');

    // Protected pages (auth required)
    Route::middleware('auth')->group(function () {
        Route::get('/dashboard', [DashboardController::class, 'index'])->name('dashboard');
        Route::post('/logout', [DashboardController::class, 'logout'])->name('logout');
        Route::get('/profile', [DashboardController::class, 'showProfile'])->name('profile');
        Route::post('/profile/update', [DashboardController::class, 'updateProfile'])->name('profile.update');
    });
});
