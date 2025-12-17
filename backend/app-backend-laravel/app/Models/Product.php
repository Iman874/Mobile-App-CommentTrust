<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Product extends Model
{
    protected $fillable = [
        'user_id',
        'product_key','shopid','itemid','name','shop_name',
        'count_reviews','avg_rating','avg_trust_score','fake_rate',
        'positive_summary','negative_summary','pros','cons','meta','tag_statistics'
    ];

    protected $casts = [
        'pros' => 'array',
        'cons' => 'array',
        'meta' => 'array',
        'tag_statistics' => 'array',
        'avg_rating' => 'float',
        'avg_trust_score' => 'float',
        'fake_rate' => 'float',
    ];

    /**
     * Get the user that owns this product
     */
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    /**
     * Get all comments for this product
     */
    public function comments(): HasMany
    {
        return $this->hasMany(Comment::class);
    }

    /**
     * Get comments filtered by tag
     */
    public function getCommentsByTag(string $tag)
    {
        return $this->comments()
            ->whereHas('commentTags', function ($query) use ($tag) {
                $query->where('tags.name', $tag);
            })
            ->orderBy('trust_score', 'desc')
            ->get();
    }

    /**
     * Get all unique tags for this product
     */
    public function getAvailableTags()
    {
        return $this->comments()
            ->whereHas('commentTags')
            ->with('commentTags')
            ->get()
            ->pluck('commentTags')
            ->flatten()
            ->unique('id')
            ->values();
    }

    /**
     * Get tag statistics (pre-calculated from Flask if available)
     */
    public function getTagStatistics(): array
    {
        // Return pre-calculated from Flask if available
        if ($this->tag_statistics) {
            return $this->tag_statistics;
        }

        // Otherwise compute from comments
        return $this->calculateTagStatistics();
    }

    /**
     * Calculate tag statistics from comments
     */
    public function calculateTagStatistics(): array
    {
        $stats = [];
        
        $this->comments()
            ->with('commentTags')
            ->get()
            ->each(function ($comment) use (&$stats) {
                foreach ($comment->commentTags as $tag) {
                    $tagName = $tag->name;
                    $stats[$tagName] = ($stats[$tagName] ?? 0) + 1;
                }
            });

        return collect($stats)
            ->sortByDesc(fn($v) => $v)
            ->toArray();
    }

    /**
     * Get most common tags
     */
    public function getTopTags(int $limit = 10): array
    {
        $stats = $this->getTagStatistics();
        return array_slice($stats, 0, $limit, true);
    }
}

