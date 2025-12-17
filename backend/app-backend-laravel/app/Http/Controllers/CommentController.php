<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use App\Models\Product;
use App\Models\Comment;
use App\Services\FlaskService;

class CommentController extends Controller
{
    private FlaskService $flaskService;

    public function __construct(FlaskService $flaskService)
    {
        $this->flaskService = $flaskService;
        $this->middleware('api_token');
    }

    /**
     * Get comments for a specific product
     * GET /api/comments/{productId}
     */
    public function index(Request $request, string $productId): JsonResponse
    {
        $user = $request->user();

        // Verify user has access to this product
        $product = Product::where('user_id', $user->id)
            ->where('product_key', $productId)
            ->orWhere(function ($q) use ($user, $productId) {
                $q->where('user_id', $user->id)
                    ->where('id', $productId);
            })
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Get query parameters
        $page = (int)$request->get('page', 1);
        $perPage = (int)$request->get('per_page', 15);
        $tags = $request->get('tags') ? explode(',', $request->get('tags')) : null;
        $sentiment = $request->get('sentiment');
        $search = $request->get('search');
        $sortBy = $request->get('sort_by', 'newest');

        // Get from Flask
        $flaskResponse = $this->flaskService->getComments(
            $product->product_key,
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

        $comments = $flaskResponse['comments'] ?? [];

        // Apply additional sorting if needed
        $comments = $this->applySorting($comments, $sortBy);

        return response()->json([
            'ok' => true,
            'product_id' => $product->id,
            'product_key' => $product->product_key,
            'comments' => $comments,
            'total_count' => $flaskResponse['total_count'] ?? 0,
            'page' => $page,
            'per_page' => $perPage,
            'tag_stats' => $flaskResponse['tag_stats'] ?? [],
            'filters_applied' => [
                'sentiment' => $sentiment,
                'tags' => $tags,
                'search' => $search,
                'sort_by' => $sortBy
            ]
        ]);
    }

    /**
     * Get single comment detail
     * GET /api/comments/{productId}/detail/{commentId}
     */
    public function show(Request $request, string $productId, string $commentId): JsonResponse
    {
        $user = $request->user();

        // Verify user has access to this product
        $product = Product::where('user_id', $user->id)
            ->where('product_key', $productId)
            ->orWhere(function ($q) use ($user, $productId) {
                $q->where('user_id', $user->id)
                    ->where('id', $productId);
            })
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Get all comments and find the one we need
        $flaskResponse = $this->flaskService->getComments($product->product_key, 1, 10000);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to get comments'
            ], 400);
        }

        $comments = $flaskResponse['comments'] ?? [];
        $comment = collect($comments)->firstWhere('comment_id', $commentId);

        if (!$comment) {
            return response()->json([
                'ok' => false,
                'message' => 'Comment not found'
            ], 404);
        }

        return response()->json([
            'ok' => true,
            'product_id' => $product->id,
            'comment' => $comment
        ]);
    }

    /**
     * Filter comments by various criteria
     * POST /api/comments/{productId}/filter
     */
    public function filter(Request $request, string $productId): JsonResponse
    {
        $request->validate([
            'sentiment' => 'nullable|in:positive,negative,neutral',
            'rating_min' => 'nullable|integer|min:1|max:5',
            'rating_max' => 'nullable|integer|min:1|max:5',
            'has_tags' => 'nullable|boolean',
            'is_fake' => 'nullable|boolean',
            'trust_score_min' => 'nullable|numeric|min:0|max:100',
            'trust_score_max' => 'nullable|numeric|min:0|max:100',
        ]);

        $user = $request->user();

        // Verify user has access to this product
        $product = Product::where('user_id', $user->id)
            ->where('product_key', $productId)
            ->orWhere(function ($q) use ($user, $productId) {
                $q->where('user_id', $user->id)
                    ->where('id', $productId);
            })
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Get all comments from Flask
        $flaskResponse = $this->flaskService->getComments($product->product_key, 1, 10000);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to get comments'
            ], 400);
        }

        $comments = collect($flaskResponse['comments'] ?? []);

        // Apply filters
        if ($request->has('sentiment') && $request->sentiment) {
            $comments = $comments->filter(function ($c) use ($request) {
                return strtolower($c['sentiment'] ?? '') === strtolower($request->sentiment);
            });
        }

        if ($request->has('rating_min') && $request->rating_min) {
            $comments = $comments->filter(function ($c) use ($request) {
                return ($c['rating_star'] ?? 0) >= $request->rating_min;
            });
        }

        if ($request->has('rating_max') && $request->rating_max) {
            $comments = $comments->filter(function ($c) use ($request) {
                return ($c['rating_star'] ?? 0) <= $request->rating_max;
            });
        }

        if ($request->has('has_tags') && $request->has_tags) {
            $comments = $comments->filter(function ($c) {
                return !empty($c['tags']);
            });
        }

        if ($request->has('is_fake') && $request->is_fake) {
            $comments = $comments->filter(function ($c) {
                return ($c['is_fake'] ?? false) == true;
            });
        }

        if ($request->has('trust_score_min') && $request->trust_score_min !== null) {
            $comments = $comments->filter(function ($c) use ($request) {
                return ($c['trust_score'] ?? 0) >= $request->trust_score_min;
            });
        }

        if ($request->has('trust_score_max') && $request->trust_score_max !== null) {
            $comments = $comments->filter(function ($c) use ($request) {
                return ($c['trust_score'] ?? 0) <= $request->trust_score_max;
            });
        }

        $filteredComments = $comments->values()->toArray();

        return response()->json([
            'ok' => true,
            'product_id' => $product->id,
            'comments' => $filteredComments,
            'count' => count($filteredComments),
            'filters_applied' => [
                'sentiment' => $request->sentiment,
                'rating_min' => $request->rating_min,
                'rating_max' => $request->rating_max,
                'has_tags' => $request->has_tags,
                'is_fake' => $request->is_fake,
                'trust_score_min' => $request->trust_score_min,
                'trust_score_max' => $request->trust_score_max
            ]
        ]);
    }

    /**
     * Search comments by text
     * GET /api/comments/{productId}/search
     */
    public function search(Request $request, string $productId): JsonResponse
    {
        $request->validate([
            'q' => 'required|string|min:2'
        ]);

        $user = $request->user();
        $query = $request->get('q');

        // Verify user has access to this product
        $product = Product::where('user_id', $user->id)
            ->where('product_key', $productId)
            ->orWhere(function ($q) use ($user, $productId) {
                $q->where('user_id', $user->id)
                    ->where('id', $productId);
            })
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Get all comments from Flask
        $flaskResponse = $this->flaskService->getComments($product->product_key, 1, 10000, null, null, $query);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to search comments'
            ], 400);
        }

        $comments = $flaskResponse['comments'] ?? [];

        return response()->json([
            'ok' => true,
            'product_id' => $product->id,
            'search_query' => $query,
            'comments' => $comments,
            'count' => count($comments)
        ]);
    }

    /**
     * Get comment statistics
     * GET /api/comments/{productId}/stats
     */
    public function stats(Request $request, string $productId): JsonResponse
    {
        $user = $request->user();

        // Verify user has access to this product
        $product = Product::where('user_id', $user->id)
            ->where('product_key', $productId)
            ->orWhere(function ($q) use ($user, $productId) {
                $q->where('user_id', $user->id)
                    ->where('id', $productId);
            })
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Get all comments from Flask
        $flaskResponse = $this->flaskService->getComments($product->product_key, 1, 10000);

        if (!$flaskResponse['ok'] ?? false) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to get comments'
            ], 400);
        }

        $comments = $flaskResponse['comments'] ?? [];

        // Calculate statistics
        $stats = [
            'total_comments' => count($comments),
            'average_rating' => $this->calculateAverageRating($comments),
            'average_trust_score' => $this->calculateAverageTrustScore($comments),
            'sentiment_distribution' => $this->calculateSentimentDistribution($comments),
            'rating_distribution' => $this->calculateRatingDistribution($comments),
            'fake_review_count' => $this->countFakeReviews($comments),
            'tagged_comment_count' => $this->countTaggedComments($comments),
            'tag_cloud' => $this->buildTagCloud($comments),
            'most_common_tags' => $this->getMostCommonTags($comments, 10),
        ];

        return response()->json([
            'ok' => true,
            'product_id' => $product->id,
            'stats' => $stats
        ]);
    }

    /**
     * Helper: Apply sorting to comments
     */
    private function applySorting(array $comments, string $sortBy): array
    {
        $collection = collect($comments);

        return match ($sortBy) {
            'rating_asc' => $collection->sortBy('rating_star')->values()->toArray(),
            'rating_desc' => $collection->sortByDesc('rating_star')->values()->toArray(),
            'trust_asc' => $collection->sortBy('trust_score')->values()->toArray(),
            'trust_desc' => $collection->sortByDesc('trust_score')->values()->toArray(),
            'newest' => $collection->sortByDesc(function ($c) {
                return strtotime($c['created_at'] ?? '0');
            })->values()->toArray(),
            'oldest' => $collection->sortBy(function ($c) {
                return strtotime($c['created_at'] ?? '0');
            })->values()->toArray(),
            default => $comments,
        };
    }

    /**
     * Helper: Calculate average rating
     */
    private function calculateAverageRating(array $comments): float
    {
        if (empty($comments)) return 0;
        $sum = array_sum(array_map(fn($c) => $c['rating_star'] ?? 0, $comments));
        return round($sum / count($comments), 2);
    }

    /**
     * Helper: Calculate average trust score
     */
    private function calculateAverageTrustScore(array $comments): float
    {
        if (empty($comments)) return 0;
        $sum = array_sum(array_map(fn($c) => $c['trust_score'] ?? 0, $comments));
        return round($sum / count($comments), 2);
    }

    /**
     * Helper: Calculate sentiment distribution
     */
    private function calculateSentimentDistribution(array $comments): array
    {
        $distribution = [
            'positive' => 0,
            'negative' => 0,
            'neutral' => 0,
        ];

        foreach ($comments as $comment) {
            $sentiment = strtolower($comment['sentiment'] ?? 'neutral');
            if (isset($distribution[$sentiment])) {
                $distribution[$sentiment]++;
            }
        }

        // Add percentages
        $total = count($comments);
        $distribution['percentages'] = [];
        foreach ($distribution as $key => $count) {
            if ($key !== 'percentages') {
                $distribution['percentages'][$key] = $total > 0 ? round(($count / $total) * 100, 2) : 0;
            }
        }

        return $distribution;
    }

    /**
     * Helper: Calculate rating distribution
     */
    private function calculateRatingDistribution(array $comments): array
    {
        $distribution = [1 => 0, 2 => 0, 3 => 0, 4 => 0, 5 => 0];

        foreach ($comments as $comment) {
            $rating = (int)($comment['rating_star'] ?? 0);
            if (isset($distribution[$rating])) {
                $distribution[$rating]++;
            }
        }

        return $distribution;
    }

    /**
     * Helper: Count fake reviews
     */
    private function countFakeReviews(array $comments): int
    {
        return array_sum(array_map(fn($c) => ($c['is_fake'] ?? false) ? 1 : 0, $comments));
    }

    /**
     * Helper: Count tagged comments
     */
    private function countTaggedComments(array $comments): int
    {
        return array_sum(array_map(fn($c) => !empty($c['tags']) ? 1 : 0, $comments));
    }

    /**
     * Helper: Build tag cloud with frequencies
     */
    private function buildTagCloud(array $comments): array
    {
        $tags = [];

        foreach ($comments as $comment) {
            if (!empty($comment['tags'])) {
                $commentTags = is_array($comment['tags']) 
                    ? $comment['tags'] 
                    : explode(',', $comment['tags']);

                foreach ($commentTags as $tag) {
                    $tag = trim($tag);
                    if ($tag) {
                        $tags[$tag] = ($tags[$tag] ?? 0) + 1;
                    }
                }
            }
        }

        arsort($tags);
        return $tags;
    }

    /**
     * Helper: Get most common tags
     */
    private function getMostCommonTags(array $comments, int $limit = 10): array
    {
        $tagCloud = $this->buildTagCloud($comments);
        return array_slice($tagCloud, 0, $limit, true);
    }

    /**
     * Get tags for a specific comment (dari relasi database)
     * GET /api/comments/{productId}/detail/{commentId}/tags
     */
    public function getCommentTags(Request $request, string $productId, string $commentId): JsonResponse
    {
        $user = $request->user();

        // Verify product belongs to user
        $product = Product::where('user_id', $user->id)
            ->where('product_key', $productId)
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Get comment with tags relation
        $comment = Comment::where('product_id', $product->id)
            ->where('id', $commentId)
            ->with('commentTags')  // Load relasi many-to-many
            ->first();

        if (!$comment) {
            return response()->json([
                'ok' => false,
                'message' => 'Comment not found'
            ], 404);
        }

        return response()->json([
            'ok' => true,
            'comment_id' => $comment->id,
            'tags_from_relation' => $comment->commentTags,  // Tags dari relasi M2M
            'tags_from_json' => $comment->tags,  // Tags dari JSON field
            'total_tags' => $comment->commentTags->count(),
        ]);
    }

    /**
     * Get all comments with their tags (dari relasi database)
     * GET /api/comments/{productId}/with-tags
     */
    public function getCommentsWithTags(Request $request, string $productId): JsonResponse
    {
        $user = $request->user();

        $product = Product::where('user_id', $user->id)
            ->where('product_key', $productId)
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        $page = (int)$request->get('page', 1);
        $perPage = (int)$request->get('per_page', 15);

        // Get comments with tags eager loaded
        $comments = Comment::where('product_id', $product->id)
            ->with(['commentTags' => function($query) {
                $query->where('is_active', true);
            }])
            ->paginate($perPage, ['*'], 'page', $page);

        return response()->json([
            'ok' => true,
            'product_id' => $productId,
            'comments' => $comments,
        ]);
    }
}
