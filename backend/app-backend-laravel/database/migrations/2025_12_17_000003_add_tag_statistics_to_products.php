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
        Schema::table('products', function (Blueprint $table) {
            // Tambahkan kolom untuk menyimpan statistik tags
            if (!Schema::hasColumn('products', 'tag_statistics')) {
                $table->json('tag_statistics')->nullable()->after('fake_rate');
            }
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('products', function (Blueprint $table) {
            if (Schema::hasColumn('products', 'tag_statistics')) {
                $table->dropColumn('tag_statistics');
            }
        });
    }
};
