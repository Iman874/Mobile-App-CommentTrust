<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\CommentTrustController;

Route::get('/', function () {
    return view('welcome');
});

// Analysis page using DB data; mirrors Flask visualisasi.html
Route::get('/analysis/{productKey}', [CommentTrustController::class, 'analysisPage']);
