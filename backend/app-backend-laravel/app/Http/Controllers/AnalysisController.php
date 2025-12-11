<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use App\Models\Product;
use App\Models\Comment;
use App\Services\FlaskService;
use Illuminate\Support\Str;

class AnalysisController extends Controller
{
    private FlaskService $flaskService;

    public function __construct(FlaskService $flaskService)
    {
        $this->flaskService = $flaskService;
        $this->middleware('api_token');
    }

    /**
     * Start full analysis (scrape + analyze) for a product URL
     * POST /api/analysis/start
     */
    public function startFullAnalysis(Request $request): JsonResponse
    {
        $request->validate([
            'product_url' => 'required|url',
        ]);

        $user = $request->user();
        $productUrl = $request->product_url;

        // Call Flask to start scraping + analysis
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

        // Store analysis job reference
        $job = [
            'job_id' => $jobId,
            'product_url' => $productUrl,
            'status' => 'queued',
            'created_at' => now(),
        ];

        // In future: persist to jobs table
        session()->put("analysis_job_{$jobId}", $job);

        return response()->json([
            'ok' => true,
            'job_id' => $jobId,
            'message' => 'Analysis started',
            'product_url' => $productUrl
        ]);
    }

    /**
     * Check analysis job status
     * GET /api/analysis/job/{jobId}
     */
    public function checkJobStatus(Request $request, string $jobId): JsonResponse
    {
        $user = $request->user();

        // Get job status from Flask
        $flaskResponse = $this->flaskService->getJobStatus($jobId);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to get job status',
                'error' => $flaskResponse['error'] ?? 'Unknown error'
            ], 400);
        }

        return response()->json([
            'ok' => true,
            'job' => $flaskResponse
        ]);
    }

    /**
     * Get all products analyzed by user
     * GET /api/analysis/products
     */
    public function getUserProducts(Request $request): JsonResponse
    {
        $user = $request->user();

        // Get products from Flask
        $flaskResponse = $this->flaskService->getProductsHistory();

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to get products',
                'error' => $flaskResponse['error'] ?? 'Unknown error'
            ], 400);
        }

        $products = $flaskResponse['products'] ?? [];

        // Enrich with database data and filter by user
        $enrichedProducts = collect($products)->map(function ($product) use ($user) {
            $dbProduct = Product::where('user_id', $user->id)
                ->where('product_key', $product['product_id'] ?? '')
                ->first();

            return array_merge($product, [
                'in_database' => !!$dbProduct,
                'db_id' => $dbProduct?->id,
                'created_at' => $dbProduct?->created_at,
                'updated_at' => $dbProduct?->updated_at,
            ]);
        })->toArray();

        return response()->json([
            'ok' => true,
            'products' => $enrichedProducts,
            'count' => count($enrichedProducts)
        ]);
    }

    /**
     * Get product statistics and analytics
     * GET /api/analysis/product/{productId}
     */
    public function getProductAnalysis(Request $request, string $productId): JsonResponse
    {
        $user = $request->user();

        // Check if user has access to this product
        $product = Product::where('user_id', $user->id)
            ->where('product_key', $productId)
            ->first();

        if (!$product && !Str::isUuid($productId)) {
            // Try Flask if not in database yet
            $flaskResponse = $this->flaskService->getProductStats($productId);

            if (!$flaskResponse['ok'] ?? false) {
                return response()->json([
                    'ok' => false,
                    'message' => 'Product not found',
                    'error' => 'Product does not exist or analysis is incomplete'
                ], 404);
            }

            return response()->json([
                'ok' => true,
                'product_id' => $productId,
                'analysis' => $flaskResponse,
                'in_database' => false
            ]);
        }

        if ($product) {
            // Get from Flask to ensure latest data
            $flaskResponse = $this->flaskService->getProductStats($productId);

            if ($flaskResponse['ok'] ?? false) {
                // Update database with latest stats
                $product->update([
                    'count_reviews' => $flaskResponse['metrics']['count_reviews'] ?? 0,
                    'avg_rating' => $flaskResponse['metrics']['avg_rating'] ?? 0,
                    'avg_trust_score' => $flaskResponse['metrics']['avg_trust_score'] ?? 0,
                    'fake_rate' => $flaskResponse['metrics']['fake_rate'] ?? 0,
                ]);
            }

            return response()->json([
                'ok' => true,
                'product_id' => $productId,
                'product' => $product,
                'analysis' => $flaskResponse,
                'in_database' => true
            ]);
        }

        return response()->json([
            'ok' => false,
            'message' => 'Unauthorized access to this product'
        ], 403);
    }

    /**
     * Get comments for a product with filtering
     * GET /api/analysis/comments/{productId}
     */
    public function getProductComments(Request $request, string $productId): JsonResponse
    {
        $user = $request->user();

        // Validate user has access
        $product = Product::where('user_id', $user->id)
            ->where('product_key', $productId)
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Unauthorized access to this product'
            ], 403);
        }

        // Get comments from database first, then enrich with Flask data
        $page = (int)$request->get('page', 1);
        $perPage = (int)$request->get('per_page', 10);
        $tags = $request->get('tags') ? explode(',', $request->get('tags')) : null;
        $sentiment = $request->get('sentiment');
        $search = $request->get('search');

        // Get from Flask API
        $flaskResponse = $this->flaskService->getComments(
            $productId,
            $page,
            $perPage,
            $tags,
            $sentiment,
            $search
        );

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to get comments',
                'error' => $flaskResponse['error'] ?? 'Unknown error'
            ], 400);
        }

        return response()->json([
            'ok' => true,
            'product_id' => $productId,
            'comments' => $flaskResponse['comments'] ?? [],
            'total_count' => $flaskResponse['total_count'] ?? 0,
            'page' => $page,
            'per_page' => $perPage,
            'tag_stats' => $flaskResponse['tag_stats'] ?? []
        ]);
    }

    /**
     * Re-analyze a product (refresh analysis from existing data)
     * POST /api/analysis/reanalyze/{productId}
     */
    public function reanalyzeProduct(Request $request, string $productId): JsonResponse
    {
        $user = $request->user();

        // Validate user has access
        $product = Product::where('user_id', $user->id)
            ->where('product_key', $productId)
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Unauthorized access to this product'
            ], 403);
        }

        // Call Flask to re-analyze
        $flaskResponse = $this->flaskService->reanalyzeProduct($productId);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to start re-analysis',
                'error' => $flaskResponse['error'] ?? 'Unknown error'
            ], 400);
        }

        return response()->json([
            'ok' => true,
            'job_id' => $flaskResponse['job_id'] ?? null,
            'message' => 'Re-analysis started',
            'product_id' => $productId
        ]);
    }

    /**
     * Scrape only (without analysis)
     * POST /api/analysis/scrape
     */
    public function scrapeOnly(Request $request): JsonResponse
    {
        $request->validate([
            'product_url' => 'required|url',
        ]);

        $user = $request->user();
        $productUrl = $request->product_url;

        // Call Flask to scrape only
        $flaskResponse = $this->flaskService->scrapeOnly($productUrl);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to start scraping',
                'error' => $flaskResponse['error'] ?? 'Unknown error'
            ], 400);
        }

        return response()->json([
            'ok' => true,
            'job_id' => $flaskResponse['job_id'] ?? null,
            'message' => 'Scraping started',
            'product_url' => $productUrl
        ]);
    }

    /**
     * Analyze only (existing scraped data)
     * POST /api/analysis/analyze/{productId}
     */
    public function analyzeOnly(Request $request, string $productId): JsonResponse
    {
        $user = $request->user();

        // Validate user has access (or product exists in Flask)
        $flaskResponse = $this->flaskService->analyzeOnly($productId);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to start analysis',
                'error' => $flaskResponse['error'] ?? 'Unknown error'
            ], 400);
        }

        return response()->json([
            'ok' => true,
            'job_id' => $flaskResponse['job_id'] ?? null,
            'message' => 'Analysis started',
            'product_id' => $productId
        ]);
    }
}
