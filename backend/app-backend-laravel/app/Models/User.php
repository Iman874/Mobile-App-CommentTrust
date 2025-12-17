<?php

namespace App\Models;

// use Illuminate\Contracts\Auth\MustVerifyEmail;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Illuminate\Support\Str;

class User extends Authenticatable
{
    /** @use HasFactory<\Database\Factories\UserFactory> */
    use HasFactory, Notifiable;

    /**
     * The attributes that are mass assignable.
     *
     * @var list<string>
     */
    protected $fillable = [
        'name',
        'email',
        'password',
        'api_token',
        'api_token_name',
        'is_guest',
        'token_expires_at',
        'is_active',
    ];

    /**
     * The attributes that should be hidden for serialization.
     *
     * @var list<string>
     */
    protected $hidden = [
        'password',
        'remember_token',
        'api_token',
    ];

    /**
     * Get the attributes that should be cast.
     *
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'last_api_used_at' => 'datetime',
            'token_expires_at' => 'datetime',
            'is_active' => 'boolean',
            'is_guest' => 'boolean',
            'password' => 'hashed',
        ];
    }

    /**
     * Generate a new API token for this user
     * For guest users: expires in 1 day
     * For regular users: no expiration
     */
    public function generateApiToken(?string $tokenName = null, bool $isGuest = false): string
    {
        $plainToken = \Illuminate\Support\Str::random(80);
        
        $updateData = [
            'api_token' => hash('sha256', $plainToken),
            'api_token_name' => $tokenName ?? 'default',
        ];
        
        // Set expiration for guest users (1 day from now)
        if ($isGuest || $this->is_guest) {
            $updateData['token_expires_at'] = now()->addDay();
        }
        
        $this->update($updateData);
        return $plainToken;
    }

    /**
     * Check if API token is still valid (not expired)
     */
    public function isTokenValid(): bool
    {
        // If no expiration set, token is valid indefinitely
        if (!$this->token_expires_at) {
            return true;
        }
        
        // Token is valid if expiration is in the future
        return now()->lessThan($this->token_expires_at);
    }

    /**
     * Check if token is expired
     */
    public function isTokenExpired(): bool
    {
        return !$this->isTokenValid();
    }

    /**
     * Get remaining token validity time in seconds
     */
    public function getTokenRemainingSeconds(): ?int
    {
        if (!$this->token_expires_at) {
            return null;
        }
        
        $remaining = now()->diffInSeconds($this->token_expires_at, false);
        return max(0, $remaining);
    }

    /**
     * Get all products for this user
     */
    public function products(): HasMany
    {
        return $this->hasMany(Product::class);
    }

    /**
     * Get all comments for this user (through products)
     */
    public function comments(): HasMany
    {
        return $this->hasMany(Comment::class);
    }

    /**
     * Update last API usage timestamp
     */
    public function recordApiUsage(): void
    {
        $this->update(['last_api_used_at' => now()]);
    }
}
