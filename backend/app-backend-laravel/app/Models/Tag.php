<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Support\Str;

class Tag extends Model
{
    protected $fillable = [
        'name',
        'slug',
        'description',
        'category',
        'color',
        'count',
        'is_active',
    ];

    protected $casts = [
        'count' => 'integer',
        'is_active' => 'boolean',
    ];

    /**
     * Get all comments tagged with this tag
     */
    public function comments(): BelongsToMany
    {
        return $this->belongsToMany(Comment::class, 'comment_tag')
                    ->withTimestamps();
    }

    /**
     * Accessor: Generate slug dari name saat simpan
     */
    public static function boot()
    {
        parent::boot();

        static::creating(function ($model) {
            if (!$model->slug) {
                $model->slug = Str::slug($model->name);
            }
        });

        static::updating(function ($model) {
            if ($model->isDirty('name') && !$model->isDirty('slug')) {
                $model->slug = Str::slug($model->name);
            }
        });
    }

    /**
     * Scope: Get only active tags
     */
    public function scopeActive($query)
    {
        return $query->where('is_active', true);
    }

    /**
     * Scope: Get tags by category
     */
    public function scopeByCategory($query, $category)
    {
        return $query->where('category', $category);
    }

    /**
     * Cari atau buat tag berdasarkan nama
     */
    public static function findOrCreateByName($name, $category = null)
    {
        return self::firstOrCreate(
            ['slug' => Str::slug($name)],
            [
                'name' => $name,
                'category' => $category,
                'is_active' => true,
            ]
        );
    }
}
