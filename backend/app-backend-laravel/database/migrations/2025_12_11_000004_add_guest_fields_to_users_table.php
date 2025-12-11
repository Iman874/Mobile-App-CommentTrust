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
            // Username field (unique)
            if (!Schema::hasColumn('users', 'username')) {
                $table->string('username')->unique()->nullable()->after('name');
            }
            
            // Guest account flag
            if (!Schema::hasColumn('users', 'is_guest')) {
                $table->boolean('is_guest')->default(false)->after('email');
            }
            
            // API token expiration timestamp
            if (!Schema::hasColumn('users', 'token_expires_at')) {
                $table->timestamp('token_expires_at')->nullable()->after('is_guest');
            }
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('users', function (Blueprint $table) {
            if (Schema::hasColumn('users', 'username')) {
                $table->dropColumn('username');
            }
            if (Schema::hasColumn('users', 'is_guest')) {
                $table->dropColumn('is_guest');
            }
            if (Schema::hasColumn('users', 'token_expires_at')) {
                $table->dropColumn('token_expires_at');
            }
        });
    }
};
