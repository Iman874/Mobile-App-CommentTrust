<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use App\Models\Product;
use App\Models\Comment;
use App\Models\Tag;

class TagController extends Controller
{
    public function __construct()
    {
        $this->middleware('api_token');
    }

    /**
     * Get all tags for a specific product
     * GET /api/products/{productId}/tags
     */
    public function getProductTags(Request $request, string $productId): JsonResponse
    {
        $user = $request->user();

        // Verify product exists and user has access
        $product = Product::where('user_id', $user->id)
            ->where('product_key', $productId)
            ->first();

        if (!$product) {
            return response()->json([
                'ok' => false,
                'message' => 'Product not found or unauthorized'
            ], 404);
        }

        // Get tags dengan count komentar dari product ini
        $tags = Tag::whereHas('comments', function ($query) use ($product) {
                $query->where('product_id', $product->id);
            })
            ->active()
            ->withCount(['comments' => function ($query) use ($product) {
                $query->where('product_id', $product->id);
            }])
            ->orderBy('comments_count', 'desc')
            ->get();

        return response()->json([
            'ok' => true,
            'tags' => $tags,
            'total' => $tags->count(),
        ]);
    }

    /**
     * Get all available tags (admin only, or active tags)
     * GET /api/tags
     */
    public function index(Request $request): JsonResponse
    {
        $category = $request->get('category');
        $active = $request->get('active', true);

        $query = Tag::query();

        if ($active) {
            $query->where('is_active', true);
        }

        if ($category) {
            $query->where('category', $category);
        }

        $tags = $query->orderBy('count', 'desc')
            ->paginate($request->get('per_page', 50));

        return response()->json([
            'ok' => true,
            'data' => $tags,
        ]);
    }

    /**
     * Get tags by category
     * GET /api/tags/by-category/{category}
     */
    public function byCategory(Request $request, string $category): JsonResponse
    {
        $tags = Tag::byCategory($category)
            ->active()
            ->orderBy('name')
            ->get();

        return response()->json([
            'ok' => true,
            'category' => $category,
            'tags' => $tags,
            'total' => $tags->count(),
        ]);
    }

    /**
     * Get comments with specific tag
     * GET /api/tags/{tagSlug}/comments
     */
    public function getTagComments(Request $request, string $tagSlug): JsonResponse
    {
        $tag = Tag::where('slug', $tagSlug)->active()->first();

        if (!$tag) {
            return response()->json([
                'ok' => false,
                'message' => 'Tag not found'
            ], 404);
        }

        $page = (int)$request->get('page', 1);
        $perPage = (int)$request->get('per_page', 15);

        $comments = $tag->comments()
            ->paginate($perPage, ['*'], 'page', $page);

        return response()->json([
            'ok' => true,
            'tag' => $tag,
            'comments' => $comments,
        ]);
    }

    /**
     * Create a new tag (admin only)
     * POST /api/tags
     */
    public function store(Request $request): JsonResponse
    {
        // Verify user is admin (if needed, add admin check)
        $validated = $request->validate([
            'name' => 'required|string|max:191',
            'description' => 'nullable|string',
            'category' => 'nullable|string|max:64',
            'color' => 'nullable|string|regex:/^#[0-9A-F]{6}$/i',
        ]);

        $tag = Tag::firstOrCreate(
            ['name' => $validated['name']],
            $validated
        );

        return response()->json([
            'ok' => true,
            'tag' => $tag,
            'message' => 'Tag created or retrieved successfully'
        ], 201);
    }

    /**
     * Update tag (admin only)
     * PUT /api/tags/{id}
     */
    public function update(Request $request, Tag $tag): JsonResponse
    {
        $validated = $request->validate([
            'name' => 'string|max:191',
            'description' => 'nullable|string',
            'category' => 'nullable|string|max:64',
            'color' => 'nullable|string|regex:/^#[0-9A-F]{6}$/i',
            'is_active' => 'boolean',
        ]);

        $tag->update($validated);

        return response()->json([
            'ok' => true,
            'tag' => $tag,
            'message' => 'Tag updated successfully'
        ]);
    }

    /**
     * Delete tag (admin only)
     * DELETE /api/tags/{id}
     */
    public function destroy(Request $request, Tag $tag): JsonResponse
    {
        // Detach dari semua comments sebelum delete
        $tag->comments()->detach();
        $tag->delete();

        return response()->json([
            'ok' => true,
            'message' => 'Tag deleted successfully'
        ]);
    }

    /**
     * Get tag statistics
     * GET /api/tags/stats/summary
     */
    public function stats(Request $request): JsonResponse
    {
        $totalTags = Tag::count();
        $activeTags = Tag::where('is_active', true)->count();
        $totalTaggedComments = Comment::whereHas('commentTags')->count();

        // Top tags
        $topTags = Tag::orderBy('count', 'desc')->limit(10)->get();

        // Tags by category
        $tagsByCategory = Tag::select('category')
            ->selectRaw('COUNT(*) as count')
            ->where('is_active', true)
            ->groupBy('category')
            ->get();

        return response()->json([
            'ok' => true,
            'stats' => [
                'total_tags' => $totalTags,
                'active_tags' => $activeTags,
                'total_tagged_comments' => $totalTaggedComments,
                'top_tags' => $topTags,
                'tags_by_category' => $tagsByCategory,
            ]
        ]);
    }
}
