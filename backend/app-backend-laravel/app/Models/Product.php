<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Product extends Model
{
    protected $fillable = [
        'product_key','shopid','itemid','name',
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

    public function comments(): HasMany
    {
        return $this->hasMany(Comment::class);
    }
}
