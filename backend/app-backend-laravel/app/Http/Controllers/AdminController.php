<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\User;
use App\Models\Product;
use App\Models\Comment;

class AdminController extends Controller
{
    /**
     * Show admin dashboard
     */
    public function dashboard()
    {
        $totalUsers = User::count();
        $guestUsers = User::where('is_guest', true)->count();
        $totalProducts = Product::count();
        $totalComments = Comment::count();
        $recentUsers = User::where('is_guest', true)
            ->orderBy('created_at', 'desc')
            ->limit(5)
            ->get();

        return view('admin.dashboard', compact(
            'totalUsers',
            'guestUsers',
            'totalProducts',
            'totalComments',
            'recentUsers'
        ));
    }

    /**
     * Get dashboard stats (API)
     */
    public function getStats()
    {
        return response()->json([
            'ok' => true,
            'stats' => [
                'total_users' => User::count(),
                'guest_users' => User::where('is_guest', true)->count(),
                'total_products' => Product::count(),
                'total_comments' => Comment::count(),
                'products_today' => Product::whereDate('created_at', today())->count(),
                'comments_today' => Comment::whereDate('created_at', today())->count(),
            ]
        ]);
    }

    /**
     * Get all products (API)
     */
    public function getProducts()
    {
        $products = Product::with('user:id,name,email')
            ->orderBy('created_at', 'desc')
            ->limit(100)
            ->get();

        return response()->json([
            'ok' => true,
            'products' => $products
        ]);
    }

    /**
     * Show API tester page
     */
    public function apiTester()
    {
        $recentTests = \DB::table('api_tests')
            ->orderBy('created_at', 'desc')
            ->limit(10)
            ->get()
            ->map(function ($test) {
                return [
                    'endpoint' => $test->endpoint,
                    'status' => $test->status,
                    'response_time' => $test->response_time,
                    'tested_at' => \Carbon\Carbon::parse($test->created_at)->format('d M Y, H:i'),
                ];
            });

        return view('admin.api-tester', compact('recentTests'));
    }

    /**
     * Get API tests log (API)
     */
    public function getApiTests()
    {
        $tests = \DB::table('api_tests')
            ->orderBy('created_at', 'desc')
            ->limit(50)
            ->get();

        return response()->json([
            'ok' => true,
            'tests' => $tests
        ]);
    }

    /**
     * Log API test result (API)
     */
    public function logApiTest(Request $request)
    {
        $request->validate([
            'endpoint' => 'required|string',
            'status' => 'required|in:success,error',
            'response_time' => 'nullable|integer',
        ]);

        \DB::table('api_tests')->insert([
            'endpoint' => $request->endpoint,
            'status' => $request->status,
            'response_time' => $request->response_time,
            'tested_by' => auth()->id(),
            'created_at' => now(),
            'updated_at' => now(),
        ]);

        return response()->json(['ok' => true]);
    }
}
