<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     *
     * Create api_tests table to log admin API testing results
     */
    public function up(): void
    {
        if (!Schema::hasTable('api_tests')) {
            Schema::create('api_tests', function (Blueprint $table) {
                $table->id();
                $table->string('endpoint');
                $table->enum('status', ['success', 'error'])->default('success');
                $table->integer('response_time')->nullable(); // milliseconds
                $table->unsignedBigInteger('tested_by')->nullable();
                $table->timestamps();

                // Indexes
                $table->index('tested_by');
                $table->index('created_at');

                // Foreign key (optional, may reference users table)
                $table->foreign('tested_by')->references('id')->on('users')->onDelete('set null');
            });
        }
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('api_tests');
    }
};
