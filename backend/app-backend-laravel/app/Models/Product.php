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
        'positive_summary','negative_summary','pros','cons','meta'
    ];

    protected $casts = [
        'pros' => 'array',
        'cons' => 'array',
        'meta' => 'array',
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
}
