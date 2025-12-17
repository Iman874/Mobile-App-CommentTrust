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
        Schema::create('comment_tag', function (Blueprint $table) {
            $table->id();
            
            // Foreign keys
            $table->foreignId('comment_id')->constrained('comments')->cascadeOnDelete();
            $table->foreignId('tag_id')->constrained('tags')->cascadeOnDelete();
            
            // Composite unique index untuk mencegah duplikat
            $table->unique(['comment_id', 'tag_id']);
            
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('comment_tag');
    }
};
