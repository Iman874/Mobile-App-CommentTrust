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
        Schema::create('tags', function (Blueprint $table) {
            $table->id();
            
            // Nama tag unik
            $table->string('name', 191)->unique()->index();
            
            // Slug untuk URL-friendly identifier
            $table->string('slug', 191)->unique()->index();
            
            // Deskripsi tag opsional
            $table->text('description')->nullable();
            
            // Kategori tag (misalnya: produk, layanan, pengiriman, kualitas, harga, dll)
            $table->string('category', 64)->nullable()->index();
            
            // Warna untuk UI (hex color code)
            $table->string('color', 7)->nullable();
            
            // Jumlah komentar dengan tag ini (denormalisasi untuk performa)
            $table->unsignedInteger('count')->default(0);
            
            // Flag untuk menandai tag sebagai aktif/inactive
            $table->boolean('is_active')->default(true)->index();
            
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('tags');
    }
};
