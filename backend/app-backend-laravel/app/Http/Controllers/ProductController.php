<?php

namespace App\Http\Controllers;

use App\Models\Product;
use Illuminate\Http\Request;

class ProductController extends Controller
{
    // GET /api/products?limit=10
    public function index(Request $request)
    {
        $limit = (int)($request->query('limit', 10));
        $limit = max(1, min(100, $limit));
        $rows = Product::orderByDesc('updated_at')
            ->limit($limit)
            ->get(['product_key','name','avg_rating']);
        return response()->json([
            'data' => $rows,
            'count' => $rows->count(),
        ]);
    }

    // GET /api/products/all  (may be large; consider pagination later)
    public function all()
    {
        $rows = Product::orderByDesc('updated_at')
            ->get(['product_key','name','avg_rating']);
        return response()->json([
            'data' => $rows,
            'count' => $rows->count(),
        ]);
    }
}
