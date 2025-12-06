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
        Schema::create('comments', function (Blueprint $table) {
            $table->id();

            // Relation to products
            $table->foreignId('product_id')->constrained('products')->cascadeOnDelete();
            $table->string('product_key', 64)->index(); // denormalized for quick lookup

            // Original review fields
            $table->string('username', 191)->nullable();
            $table->text('comment')->nullable();
            $table->decimal('rating', 3, 2)->nullable();
            $table->unsignedInteger('likes')->default(0);
            $table->unsignedBigInteger('create_time')->nullable(); // epoch from source
            $table->dateTime('commented_at')->nullable(); // optional parsed datetime

            // Preprocessing
            $table->text('comment_clean')->nullable();
            $table->longText('tokens')->nullable();
            $table->unsignedInteger('tokens_count')->nullable();

            // Sentiment
            $table->string('sentiment', 16)->nullable()->index();
            $table->decimal('sentiment_confidence', 6, 4)->nullable();

            // Fake review detection
            $table->boolean('fake_pred')->default(false);
            $table->decimal('fake_score', 6, 4)->nullable()->index();

            // Trust
            $table->decimal('trust_score', 6, 2)->nullable()->index();

            // Extra derived metrics (optional in CSV)
            $table->unsignedInteger('text_len')->nullable();
            $table->decimal('char_repeat_ratio', 8, 6)->nullable();
            $table->decimal('token_repeat_ratio', 8, 6)->nullable();
            $table->decimal('dup_score', 8, 6)->nullable();
            $table->boolean('mismatch')->nullable();

            // Product variant/label hints
            $table->string('product_label', 191)->nullable();
            $table->string('variant_name', 191)->nullable();

            // Extensibility for any backend-specific fields
            $table->json('extras')->nullable();

            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('comments');
    }
};
