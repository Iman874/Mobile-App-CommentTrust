<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Comment extends Model
{
    protected $fillable = [
        'user_id',
        'product_id','product_key','username','comment','rating','likes','create_time','commented_at',
        'comment_clean','tokens','tokens_count','sentiment','sentiment_confidence',
        'fake_pred','fake_score','trust_score','text_len','char_repeat_ratio','token_repeat_ratio','dup_score','mismatch',
        'product_label','variant_name','tags','extras'
    ];

    protected $casts = [
        'rating' => 'float',
        'sentiment_confidence' => 'float',
        'fake_pred' => 'boolean',
        'fake_score' => 'float',
        'trust_score' => 'float',
        'commented_at' => 'datetime',
        'extras' => 'array',
        'tags' => 'array',
    ];

    /**
     * Get the user that owns this comment (through product)
     */
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    /**
     * Get the product this comment belongs to
     */
    public function product(): BelongsTo
    {
        return $this->belongsTo(Product::class);
    }
}
