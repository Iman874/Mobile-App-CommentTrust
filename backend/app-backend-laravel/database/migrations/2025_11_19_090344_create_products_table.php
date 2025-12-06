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
        Schema::create('products', function (Blueprint $table) {
            $table->id();
            // Key identifiers
            $table->string('product_key', 64)->unique(); // e.g. "shopid-itemid"
            $table->unsignedBigInteger('shopid')->nullable()->index();
            $table->unsignedBigInteger('itemid')->nullable()->index();

            // Basic product info
            $table->string('name', 512)->nullable();

            // Aggregated metrics from analysis
            $table->unsignedInteger('count_reviews')->default(0);
            $table->decimal('avg_rating', 4, 2)->nullable();
            $table->decimal('avg_trust_score', 6, 2)->nullable();
            $table->decimal('fake_rate', 6, 4)->nullable();

            // Summaries
            $table->text('positive_summary')->nullable();
            $table->text('negative_summary')->nullable();
            $table->json('pros')->nullable();
            $table->json('cons')->nullable();

            // Optional raw payload/meta (from product.json)
            $table->json('meta')->nullable();

            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('products');
    }
};
