<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\CommentTrustController;
use App\Http\Controllers\ProductController;
use App\Http\Controllers\CommentController;
use App\Http\Controllers\AnalysisController;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\GuestAuthController;
use App\Http\Controllers\AdminController;
use App\Http\Controllers\UserManagementController;
use App\Http\Controllers\JobManagementController;

// ============================================================================
// Public Routes (No Authentication)
// ============================================================================
Route::get('/ping', function() {
    return response()->json(['ok' => true, 'status' => 'ok']);
});

// Regular Authentication endpoints
Route::prefix('/auth')->group(function () {
    Route::post('/register', [AuthController::class, 'register']);
    Route::post('/login', [AuthController::class, 'login']);
});

// Guest Authentication endpoints (Public)
Route::prefix('/guest')->group(function () {
    Route::post('/login', [GuestAuthController::class, 'loginAsGuest']);
    Route::get('/list', [GuestAuthController::class, 'listGuests']);
    Route::post('/login-as-existing', [GuestAuthController::class, 'loginAsExistingGuest']);
});

// ============================================================================
// Protected Routes (Require API Token via api_token middleware)
// ============================================================================
Route::middleware(['api_token', 'check_token_expiration'])->group(function () {
    // ========================================================================
    // Authentication - Token Management
    // ========================================================================
    Route::prefix('/auth')->group(function () {
        Route::get('/me', [AuthController::class, 'me']);
        Route::post('/logout', [AuthController::class, 'logout']);
        Route::post('/profile/update', [AuthController::class, 'updateProfile']);
        Route::post('/token/generate', [AuthController::class, 'generateNewToken']);
        Route::post('/token/revoke', [AuthController::class, 'revokeToken']);
        Route::post('/token/validate', [AuthController::class, 'validateToken']);
    });

    // Guest account management (for authenticated guests)
    Route::prefix('/guest')->group(function () {
        Route::post('/refresh-token', [GuestAuthController::class, 'refreshGuestToken']);
        Route::get('/token-status', [GuestAuthController::class, 'checkTokenStatus']);
        Route::post('/convert-to-user', [GuestAuthController::class, 'convertToRegularUser']);
        Route::post('/logout', [GuestAuthController::class, 'logoutGuest']);
    });

    // ========================================================================
    // Products Management
    // ========================================================================
    Route::prefix('/products')->group(function () {
        Route::get('/', [ProductController::class, 'index']);              // List user products
        Route::post('/', [ProductController::class, 'store']);            // Create/start analysis
        Route::get('/{id}', [ProductController::class, 'show']);          // Get product details
        Route::put('/{id}', [ProductController::class, 'update']);        // Update product
        Route::delete('/{id}', [ProductController::class, 'destroy']);    // Delete product
        Route::get('/{id}/stats', [ProductController::class, 'getStats']);
        Route::get('/{id}/sentiment-breakdown', [ProductController::class, 'getSentimentBreakdown']);
        Route::get('/{id}/rating-distribution', [ProductController::class, 'getRatingDistribution']);
    });

    // ========================================================================
    // Comments Management
    // ========================================================================
    Route::prefix('/comments')->group(function () {
        Route::get('/{productId}', [CommentController::class, 'index']);          // List comments
        Route::get('/{productId}/detail/{commentId}', [CommentController::class, 'show']);
        Route::post('/{productId}/filter', [CommentController::class, 'filter']);  // Advanced filtering
        Route::get('/{productId}/search', [CommentController::class, 'search']);   // Text search
        Route::get('/{productId}/stats', [CommentController::class, 'stats']);     // Comment statistics
    });

    // ========================================================================
    // Analysis & Jobs
    // ========================================================================
    Route::prefix('/analysis')->group(function () {
        // Job Management
        Route::get('/job/{jobId}', [AnalysisController::class, 'checkJobStatus']);

        // Product Analysis
        Route::get('/products', [AnalysisController::class, 'getUserProducts']);
        Route::get('/product/{productId}', [AnalysisController::class, 'getProductAnalysis']);
        Route::get('/product/{productId}/comments', [AnalysisController::class, 'getProductComments']);

        // Analysis Operations
        Route::post('/start', [AnalysisController::class, 'startFullAnalysis']);
        Route::post('/scrape', [AnalysisController::class, 'scrapeOnly']);
        Route::post('/analyze/{productId}', [AnalysisController::class, 'analyzeOnly']);
        Route::post('/reanalyze/{productId}', [AnalysisController::class, 'reanalyzeProduct']);
    });
});

// ============================================================================
// Admin Routes (Require Authentication & Admin Role)
// ============================================================================
// Admin routes should also honor API token expiration rules
Route::middleware(['auth', 'admin', 'check_token_expiration'])->prefix('/admin')->group(function () {
    // Dashboard & Stats
    Route::get('/stats', [AdminController::class, 'getStats']);

    // User Management
    Route::get('/users', [UserManagementController::class, 'list']);
    Route::get('/users/{id}', [UserManagementController::class, 'show']);
    Route::put('/users/{id}', [UserManagementController::class, 'update']);
    Route::delete('/users/{id}', [UserManagementController::class, 'destroy']);
    Route::post('/users/{id}/refresh-token', [UserManagementController::class, 'refreshToken']);
    Route::post('/users/{id}/extend-token', [UserManagementController::class, 'extendToken']);
    Route::post('/users/{id}/reset-sessions', [UserManagementController::class, 'resetSessions']);

    // Admin self-token management (tokens expire after 24 hours)
    Route::post('/token/generate', [AdminController::class, 'generateAdminToken']);
    Route::post('/token/revoke', [AdminController::class, 'revokeAdminToken']);

    // Job Management
    Route::get('/jobs', [JobManagementController::class, 'list']);
    Route::post('/jobs/{id}/retry', [JobManagementController::class, 'retryJob']);
    Route::delete('/jobs/{id}/cancel', [JobManagementController::class, 'cancelJob']);
    Route::delete('/jobs/{id}', [JobManagementController::class, 'deleteJob']);

    // Products
    Route::get('/products', [AdminController::class, 'getProducts']);

    // API Tests
    Route::get('/api-tests', [AdminController::class, 'getApiTests']);
    Route::post('/api-tests', [AdminController::class, 'logApiTest']);
});

// ============================================================================
// Legacy Routes (kept for backward compatibility with Flask ingestion)
// ============================================================================
Route::middleware('api')->group(function() {
    // Webhook from Flask to ingest results
    Route::post('/ingest/commenttrust', [CommentTrustController::class, 'ingest']);

    // Analysis JSON for frontend UI
    Route::get('/analysis/{productKey}', [CommentTrustController::class, 'analysisJson']);

    // Frontend consumption endpoints
    Route::get('/products/latest', [CommentTrustController::class, 'productsLatest']);
    Route::get('/products/{productKey}/comments', [CommentTrustController::class, 'commentsForProduct']);
    Route::get('/products/{productKey}/tags', [CommentTrustController::class, 'tagsForProduct']);
});
