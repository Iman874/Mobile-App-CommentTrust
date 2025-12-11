<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use App\Models\Product;
use App\Models\Comment;
use App\Services\FlaskService;

class ProductController extends Controller
{
    private FlaskService $flaskService;

    public function __construct(FlaskService $flaskService)
    {
        $this->flaskService = $flaskService;
        $this->middleware('api_token');
    }

    /**
     * Get all products for authenticated user
     * GET /api/products
     */
    public function index(Request $request): JsonResponse
    {
        $user = $request->user();
        $page = (int)$request->get('page', 1);
        $perPage = (int)$request->get('per_page', 10);
        $search = $request->get('search');

        $query = Product::where('user_id', $user->id);

        // Search by name or product_key
        if ($search) {
            $query->where(function ($q) use ($search) {
                $q->where('name', 'like', "%{$search}%")
                    ->orWhere('product_key', 'like', "%{$search}%");
            });
        }

        // Get total count before pagination
        $total = $query->count();

        // Apply pagination
        $products = $query->orderBy('created_at', 'desc')
            ->paginate($perPage, ['*'], 'page', $page);

        return response()->json([
            'ok' => true,
            'products' => $products->items(),
            'pagination' => [
                'total' => $total,
                'per_page' => $perPage,
                'current_page' => $page,
                'last_page' => $products->lastPage(),
                'from' => $products->firstItem(),
                'to' => $products->lastItem(),
            ]
        ]);
    }

    /**
     * Create new product/start analysis job
     * POST /api/products
     */
    public function store(Request $request): JsonResponse
    {
        $request->validate([
            'product_url' => 'required|url',
        ]);

        $user = $request->user();
        $productUrl = $request->product_url;

        // Call Flask API to start analysis
        $flaskResponse = $this->flaskService->analyzeFullUrl($productUrl);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to start analysis',
                'error' => $flaskResponse['error'] ?? 'Unknown error'
            ], 400);
        }

        $jobId = $flaskResponse['job_id'] ?? null;

        if (!$jobId) {
            return response()->json([
                'ok' => false,
                'message' => 'No job ID returned from Flask'
            ], 400);
        }

        // In production: Store job tracking in database
        // For now, return job ID for polling
        return response()->json([
            'ok' => true,
            'job_id' => $jobId,
            'message' => 'Analysis job started',
            'product_url' => $productUrl,
            'check_status_url' => "/api/analysis/job/{$jobId}"
        ], 201);
    }

    /**
     * Get specific product details
     * GET /api/products/{id}
     */
    public function show(Request $request, string $id): JsonResponse
    {
        $user = $request->user();

        // Get from database
        $product = Product::where('user_id', $user->id)
            ->where('id', $id)
            ->orWhere(function ($q) use ($user, $id) {
                $q->where('user_id', $user->id)
                    ->where('product_key', $id);
            })
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Get latest stats from Flask
        $flaskStats = $this->flaskService->getProductStats($product->product_key);

        return response()->json([
            'ok' => true,
            'product' => $product,
            'stats' => $flaskStats['ok'] ? $flaskStats : null
        ]);
    }

    /**
     * Update product details
     * PUT /api/products/{id}
     */
    public function update(Request $request, string $id): JsonResponse
    {
        $request->validate([
            'name' => 'nullable|string|max:255',
            'notes' => 'nullable|string',
        ]);

        $user = $request->user();

        $product = Product::where('user_id', $user->id)
            ->where('id', $id)
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Only allow updating certain fields
        if ($request->has('name')) {
            $product->name = $request->name;
        }
        if ($request->has('notes')) {
            $product->notes = $request->notes;
        }

        $product->save();

        return response()->json([
            'ok' => true,
            'product' => $product,
            'message' => 'Product updated'
        ]);
    }

    /**
     * Delete product
     * DELETE /api/products/{id}
     */
    public function destroy(Request $request, string $id): JsonResponse
    {
        $user = $request->user();

        $product = Product::where('user_id', $user->id)
            ->where('id', $id)
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Also delete related comments
        Comment::where('product_id', $product->id)
            ->where('user_id', $user->id)
            ->delete();

        $product->delete();

        return response()->json([
            'ok' => true,
            'message' => 'Product and related comments deleted'
        ]);
    }

    /**
     * Get product statistics/metrics
     * GET /api/products/{id}/stats
     */
    public function getStats(Request $request, string $id): JsonResponse
    {
        $user = $request->user();

        // Verify ownership
        $product = Product::where('user_id', $user->id)
            ->where('id', $id)
            ->orWhere(function ($q) use ($user, $id) {
                $q->where('user_id', $user->id)
                    ->where('product_key', $id);
            })
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Get stats from Flask
        $flaskResponse = $this->flaskService->getProductStats($product->product_key);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to get statistics',
                'error' => $flaskResponse['error'] ?? 'Unknown error'
            ], 400);
        }

        return response()->json([
            'ok' => true,
            'product_id' => $product->id,
            'product_key' => $product->product_key,
            'stats' => $flaskResponse
        ]);
    }

    /**
     * Get comment count by sentiment
     * GET /api/products/{id}/sentiment-breakdown
     */
    public function getSentimentBreakdown(Request $request, string $id): JsonResponse
    {
        $user = $request->user();

        // Verify ownership
        $product = Product::where('user_id', $user->id)
            ->where('id', $id)
            ->orWhere(function ($q) use ($user, $id) {
                $q->where('user_id', $user->id)
                    ->where('product_key', $id);
            })
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Get comments to analyze sentiment breakdown
        $flaskResponse = $this->flaskService->getComments($product->product_key, 1, 1000);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to get comments'
            ], 400);
        }

        $comments = $flaskResponse['comments'] ?? [];

        // Build sentiment breakdown
        $breakdown = [
            'positive' => 0,
            'negative' => 0,
            'neutral' => 0,
            'unknown' => 0
        ];

        foreach ($comments as $comment) {
            $sentiment = strtolower($comment['sentiment'] ?? 'unknown');
            if (isset($breakdown[$sentiment])) {
                $breakdown[$sentiment]++;
            } else {
                $breakdown['unknown']++;
            }
        }

        $total = count($comments);
        $percentages = [];
        foreach ($breakdown as $type => $count) {
            $percentages[$type] = $total > 0 ? round(($count / $total) * 100, 2) : 0;
        }

        return response()->json([
            'ok' => true,
            'product_id' => $product->id,
            'sentiment_breakdown' => $breakdown,
            'sentiment_percentages' => $percentages,
            'total_comments' => $total
        ]);
    }

    /**
     * Get rating distribution
     * GET /api/products/{id}/rating-distribution
     */
    public function getRatingDistribution(Request $request, string $id): JsonResponse
    {
        $user = $request->user();

        // Verify ownership
        $product = Product::where('user_id', $user->id)
            ->where('id', $id)
            ->orWhere(function ($q) use ($user, $id) {
                $q->where('user_id', $user->id)
                    ->where('product_key', $id);
            })
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Get comments to analyze rating distribution
        $flaskResponse = $this->flaskService->getComments($product->product_key, 1, 1000);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to get comments'
            ], 400);
        }

        $comments = $flaskResponse['comments'] ?? [];

        // Build rating distribution
        $distribution = [
            1 => 0,
            2 => 0,
            3 => 0,
            4 => 0,
            5 => 0
        ];

        foreach ($comments as $comment) {
            $rating = (int)($comment['rating_star'] ?? 0);
            if (isset($distribution[$rating])) {
                $distribution[$rating]++;
            }
        }

        $total = count($comments);
        $percentages = [];
        foreach ($distribution as $rating => $count) {
            $percentages[$rating] = $total > 0 ? round(($count / $total) * 100, 2) : 0;
        }

        return response()->json([
            'ok' => true,
            'product_id' => $product->id,
            'rating_distribution' => $distribution,
            'rating_percentages' => $percentages,
            'total_comments' => $total,
            'average_rating' => $total > 0 ? round(array_sum(array_map(fn($c) => $c['rating_star'] ?? 0, $comments)) / $total, 2) : 0
        ]);
    }
}
