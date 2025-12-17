<?php

namespace App\Services;

use App\Models\Comment;
use App\Models\Tag;
use App\Models\Product;
use Illuminate\Support\Facades\Log;
use Carbon\Carbon;

class TagService
{
    /**
     * Attach tags ke comments berdasarkan tags string (pipe-separated atau array)
     * 
     * @param Comment $comment Comment model
     * @param string|array $tags Tags dalam format pipe-separated atau array
     * @param string|null $category Kategori untuk tag baru
     * @return void
     */
    public function attachTagsToComment(Comment $comment, $tags, $category = null): void
    {
        if (empty($tags)) {
            return;
        }

        try {
            // Parse tags if string
            $tagNames = is_array($tags) ? $tags : array_map('trim', explode('|', (string)$tags));
            $tagNames = array_filter($tagNames); // Remove empty values

            if (empty($tagNames)) {
                return;
            }

            Log::debug("Attaching tags to comment {$comment->id}", [
                'tag_names' => $tagNames,
                'count' => count($tagNames),
            ]);

            $comment->syncTagsByName($tagNames, $category);

            Log::debug("Tags attached successfully to comment {$comment->id}");
        } catch (\Exception $e) {
            Log::warning("Failed to attach tags to comment {$comment->id}", [
                'error' => $e->getMessage(),
                'tags' => $tags,
            ]);
        }
    }

    /**
     * Process tags CSV data dari Flask dan attach ke comments
     * 
     * @param array $tagsCsvData Array of tag data from Flask (tags_csv)
     * @param Product $product Product yang sedang diproses
     * @param string|null $category Kategori untuk tag baru
     * @return array Statistics tentang tags yang diproses
     */
    public function processTagsCsvData(array $tagsCsvData, Product $product, $category = null): array
    {
        $stats = [
            'total_processed' => 0,
            'total_tags_attached' => 0,
            'comments_with_tags' => 0,
            'errors' => 0,
            'skipped' => 0,
        ];

        if (empty($tagsCsvData)) {
            Log::info("No tags CSV data to process for product {$product->id}");
            return $stats;
        }

        Log::info("Processing tags CSV data", [
            'product_id' => $product->id,
            'items_count' => count($tagsCsvData),
        ]);

        foreach ($tagsCsvData as $index => $item) {
            try {
                $stats['total_processed']++;

                $comment = $item['comment'] ?? $item['comment_text'] ?? null;
                $tags = $item['tags'] ?? null;

                if (empty($comment) || empty($tags)) {
                    $stats['skipped']++;
                    Log::debug("Skipped item {$index} - missing comment or tags", [
                        'has_comment' => !empty($comment),
                        'has_tags' => !empty($tags),
                    ]);
                    continue;
                }

                // Find comment in this product
                $commentModel = $product->comments()
                    ->where('comment', $comment)
                    ->first();

                if (!$commentModel) {
                    Log::debug("Comment not found for item {$index}", [
                        'comment_preview' => substr($comment, 0, 50),
                    ]);
                    $stats['skipped']++;
                    continue;
                }

                // Attach tags
                $this->attachTagsToComment($commentModel, $tags, $category);

                // Parse tags to count
                $tagNames = is_array($tags) ? $tags : array_map('trim', explode('|', (string)$tags));
                $tagNames = array_filter($tagNames);

                if (!empty($tagNames)) {
                    $stats['comments_with_tags']++;
                    $stats['total_tags_attached'] += count($tagNames);
                }

            } catch (\Exception $e) {
                $stats['errors']++;
                Log::warning("Error processing tags CSV item {$index}", [
                    'error' => $e->getMessage(),
                ]);
            }
        }

        Log::info("Completed processing tags CSV data", $stats);

        return $stats;
    }

    /**
     * Update product dengan tag statistics dari Flask
     * 
     * @param Product $product Product model
     * @param array $tagStatistics Tag statistics dari Flask
     * @return void
     */
    public function updateProductTagStatistics(Product $product, array $tagStatistics = null): void
    {
        try {
            if (empty($tagStatistics)) {
                // Calculate dari comments jika tidak disediakan
                $tagStatistics = $product->calculateTagStatistics();
            }

            $product->update([
                'tag_statistics' => $tagStatistics,
            ]);

            Log::info("Updated product tag statistics", [
                'product_id' => $product->id,
                'unique_tags' => count($tagStatistics),
                'total_tag_count' => array_sum($tagStatistics),
            ]);
        } catch (\Exception $e) {
            Log::warning("Failed to update product tag statistics", [
                'product_id' => $product->id,
                'error' => $e->getMessage(),
            ]);
        }
    }

    /**
     * Sync semua comments dalam product dengan tags berdasarkan tags column
     * Gunakan untuk migrate dari pipe-separated tags string ke many-to-many relationship
     * 
     * @param Product $product Product model
     * @param string|null $category Kategori untuk tag baru
     * @return array Statistics
     */
    public function syncAllCommentsTags(Product $product, $category = null): array
    {
        $stats = [
            'total_comments' => 0,
            'comments_processed' => 0,
            'total_tags_attached' => 0,
            'errors' => 0,
        ];

        Log::info("Starting sync all comments tags for product {$product->id}");

        try {
            $comments = $product->comments()->get();
            $stats['total_comments'] = $comments->count();

            foreach ($comments as $comment) {
                try {
                    $tags = $comment->tags; // This is the JSON array field

                    if (empty($tags)) {
                        continue;
                    }

                    // Convert to array if needed
                    $tagNames = is_array($tags) ? $tags : array_map('trim', explode('|', (string)$tags));
                    $tagNames = array_filter($tagNames);

                    if (empty($tagNames)) {
                        continue;
                    }

                    $this->attachTagsToComment($comment, $tagNames, $category);

                    $stats['comments_processed']++;
                    $stats['total_tags_attached'] += count($tagNames);

                } catch (\Exception $e) {
                    $stats['errors']++;
                    Log::warning("Error syncing tags for comment {$comment->id}", [
                        'error' => $e->getMessage(),
                    ]);
                }
            }

            Log::info("Completed sync all comments tags for product {$product->id}", $stats);

        } catch (\Exception $e) {
            Log::error("Failed to sync all comments tags", [
                'product_id' => $product->id,
                'error' => $e->getMessage(),
            ]);
        }

        return $stats;
    }

    /**
     * Get tag statistics untuk product
     * Preference: pre-calculated > calculated dari comments
     * 
     * @param Product $product Product model
     * @return array Tag statistics
     */
    public function getProductTagStatistics(Product $product): array
    {
        return $product->getTagStatistics();
    }

    /**
     * Get tags yang paling sering muncul
     * 
     * @param Product $product Product model
     * @param int $limit Jumlah top tags yang ingin diambil
     * @return array Top tags dengan count-nya
     */
    public function getTopTags(Product $product, int $limit = 10): array
    {
        return $product->getTopTags($limit);
    }

    /**
     * Create tag jika tidak ada
     * 
     * @param string $name Nama tag
     * @param string|null $category Kategori tag
     * @param string|null $description Deskripsi tag
     * @return Tag
     */
    public function createTagIfNotExists(string $name, string $category = null, string $description = null): Tag
    {
        return Tag::findOrCreateByName($name, $category);
    }

    /**
     * Bulk create tags
     * 
     * @param array $tagNames Array of tag names
     * @param string|null $category Category untuk semua tags
     * @return array Array of created/found Tag models
     */
    public function createTagsIfNotExist(array $tagNames, string $category = null): array
    {
        $tags = [];

        foreach ($tagNames as $name) {
            $tags[] = $this->createTagIfNotExists($name, $category);
        }

        return $tags;
    }
}
