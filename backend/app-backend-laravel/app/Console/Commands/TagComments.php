<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\Comment;
use App\Models\Product;
use App\Models\Tag;

class TagComments extends Command
{
    protected $signature = 'comments:tag {product_id?} {--force : Force re-tag existing tags}';
    protected $description = 'Auto-tag comments berdasarkan sentiment, trust score, dan rating';

    public function handle()
    {
        $productId = $this->argument('product_id');
        $force = $this->option('force');

        if ($productId) {
            // Tag specific product
            $this->tagProduct($productId, $force);
        } else {
            // Tag all products
            $products = Product::all();
            $this->info("Found {$products->count()} products");
            
            foreach ($products as $product) {
                $this->tagProduct($product->product_key, $force);
            }
        }

        $this->info("Tagging completed!");
    }

    private function tagProduct($productKey, $force = false)
    {
        $product = Product::where('product_key', $productKey)->first();
        
        if (!$product) {
            $this->error("Product not found: {$productKey}");
            return;
        }

        $this->line("\nTagging product: {$product->name} ({$productKey})");
        
        $query = Comment::where('product_id', $product->id);
        
        // Skip already tagged comments jika tidak force
        if (!$force) {
            $query->doesntHave('commentTags');
        }
        
        $totalComments = $query->count();
        
        if ($totalComments === 0) {
            $this->info("No comments to tag for this product");
            return;
        }

        $this->info("Processing {$totalComments} comments...");
        
        $bar = $this->output->createProgressBar($totalComments);
        $bar->start();
        
        $taggedCount = 0;
        $errorCount = 0;

        $query->chunk(100, function ($comments) use (&$taggedCount, &$errorCount, &$bar, $force) {
            foreach ($comments as $comment) {
                try {
                    $tags = $this->generateTags($comment);
                    
                    if (!empty($tags)) {
                        if ($force) {
                            $comment->syncTagsByName($tags);
                        } else {
                            $comment->attachTagsByName($tags);
                        }
                        $taggedCount++;
                    }
                } catch (\Exception $e) {
                    $errorCount++;
                    $this->warn("Error tagging comment {$comment->id}: {$e->getMessage()}");
                }
                
                $bar->advance();
            }
        });

        $bar->finish();
        $this->newLine();
        
        $this->info("Tagged: {$taggedCount}, Errors: {$errorCount}");
    }

    private function generateTags($comment): array
    {
        $tags = [];

        // ============== SENTIMENT TAGS ==============
        if ($comment->sentiment) {
            switch (strtolower($comment->sentiment)) {
                case 'positive':
                    $tags[] = 'Kualitas Baik';
                    break;
                case 'negative':
                    $tags[] = 'Kualitas Jelek';
                    break;
                case 'neutral':
                    // Tidak add tag untuk neutral
                    break;
            }
        }

        // ============== TRUST SCORE TAGS ==============
        if (!is_null($comment->trust_score)) {
            $score = (float) $comment->trust_score;
            
            if ($score >= 80) {
                $tags[] = 'Terpercaya';
            } elseif ($score <= 30) {
                $tags[] = 'Mencurigakan';
            }
        }

        // ============== RATING TAGS ==============
        if (!is_null($comment->rating)) {
            $rating = (float) $comment->rating;
            
            if ($rating >= 4) {
                $tags[] = 'Rating Tinggi';
            } elseif ($rating <= 2) {
                $tags[] = 'Rating Rendah';
            }
        }

        // ============== FAKE DETECTION TAGS ==============
        if ($comment->fake_pred) {
            $tags[] = 'Mencurigakan';
        }

        // ============== TEXT LENGTH TAGS ==============
        if (!is_null($comment->text_len)) {
            if ($comment->text_len >= 200) {
                $tags[] = 'Ulasan Detail';
            } elseif ($comment->text_len <= 30) {
                $tags[] = 'Ulasan Singkat';
            }
        }

        // ============== DUPLICATE SCORE TAGS ==============
        if (!is_null($comment->dup_score)) {
            $dup = (float) $comment->dup_score;
            if ($dup >= 0.7) {
                $tags[] = 'Mencurigakan'; // Likely copy-paste
            }
        }

        // ============== ENGAGEMENT TAGS ==============
        if (!is_null($comment->likes)) {
            if ($comment->likes >= 100) {
                $tags[] = 'Ulasan Populer';
            }
        }

        // Remove duplicates
        $tags = array_unique($tags);

        return $tags;
    }
}
