<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\CommentTrustController;
use App\Http\Controllers\ProductController;

Route::middleware('api')->group(function(){
    Route::get('/ping', function(){ return response()->json(['status'=>'ok']); });
    // Webhook from Flask to ingest results
    Route::post('/ingest/commenttrust', [CommentTrustController::class, 'ingest']);

    // Analysis JSON for frontend UI
    Route::get('/analysis/{productKey}', [CommentTrustController::class, 'analysisJson']);

    // Frontend consumption endpoints
    Route::get('/products/latest', [CommentTrustController::class, 'productsLatest']);
    Route::get('/products/{productKey}/comments', [CommentTrustController::class, 'commentsForProduct']);
    Route::get('/products/{productKey}/tags', [CommentTrustController::class, 'tagsForProduct']);
    Route::get('/products', [ProductController::class, 'index']);
    Route::get('/products/all', [ProductController::class, 'all']);
});
