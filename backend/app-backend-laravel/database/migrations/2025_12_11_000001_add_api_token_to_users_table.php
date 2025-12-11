<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table) {
            // API token for authentication (unique per user)
            if (!Schema::hasColumn('users', 'api_token')) {
                $table->string('api_token')->unique()->nullable();
            }
            
            // API token name/label (for tracking which app/device created it)
            if (!Schema::hasColumn('users', 'api_token_name')) {
                $table->string('api_token_name')->nullable();
            }
            
            // Track last API usage
            if (!Schema::hasColumn('users', 'last_api_used_at')) {
                $table->timestamp('last_api_used_at')->nullable();
            }
            
            // Enable/disable user access
            if (!Schema::hasColumn('users', 'is_active')) {
                $table->boolean('is_active')->default(true);
            }
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->dropColumn(['api_token', 'api_token_name', 'last_api_used_at', 'is_active']);
        });
    }
};
