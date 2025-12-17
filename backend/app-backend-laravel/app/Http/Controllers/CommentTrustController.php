<?php

namespace App\Http\Controllers;

use App\Models\Product;
use App\Models\Comment;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Carbon\Carbon;

class CommentTrustController extends Controller
{
    private function flaskBase(): string
    {
        return rtrim(env('FLASK_BASE_URL', 'http://127.0.0.1:5001/api'), '/');
    }

    public function ingest(Request $request)
    {
        $productKey = $request->input('product_id');
        $force = (bool)$request->boolean('force', false);
        $userId = $request->input('user_id');
        
        \Illuminate\Support\Facades\Log::info('CommentTrustController::ingest', [
            'product_id' => $productKey,
            'user_id' => $userId,
            'force' => $force,
        ]);
        
        if (!$productKey) {
            return response()->json(['error' => 'missing product_id'], 400);
        }

        $exists = Product::where('product_key', $productKey)->exists();
        $existingComments = Comment::where('product_key', $productKey)->count();
        if ($exists && !$force && $existingComments > 0) {
            // tell Flask we are using cached DB
            try {
                Http::post($this->flaskBase() . '/log', [
                    'message' => "Laravel: data exists for {$productKey}; using cached DB (no overwrite)"
                ]);
            } catch (\Throwable $e) {
                Log::warning('Notify Flask log failed: ' . $e->getMessage());
            }
            return response()->json(['ok' => true, 'message' => 'already ingested; skip (no force)']);
        }

        // Pull all artifacts from Flask
        $url = $this->flaskBase() . "/result/{$productKey}/all";
        $resp = Http::timeout(120)->withHeaders(['Accept'=>'application/json'])->get($url);
        $body = $resp->body();
        $status = $resp->status();
        $len = strlen($body ?? '');
        Log::info("Raw Flask response status={$status} len={$len} product={$productKey} first300=" . substr($body ?? '',0,300));
        if (!$resp->ok()) {
            return response()->json(['error' => 'failed to fetch from Flask', 'status' => $resp->status()], 502);
        }
        // Manual decode to inspect json errors
        $data = json_decode($body, true);
        if ($data === null) {
            $err = json_last_error_msg();
            Log::warning("JSON decode null product={$productKey} error={$err}; attempting sanitize replace");
            // Replace NaN / Infinity tokens (unquoted) with null, retry
            $body2 = preg_replace('/\bNaN\b|\bInfinity\b|\b-Infinity\b/', 'null', $body);
            $data = json_decode($body2, true);
            if ($data === null) {
                return response()->json(['error'=>'json decode failed','json_error'=>$err], 502);
            }
            Log::info("JSON sanitize success product={$productKey}");
        }
        // Extra diagnostics: key existence + raw counts before casting
        $hasTrust = array_key_exists('trust', $data);
        $hasSent = array_key_exists('sentiment', $data);
        $hasRaw = array_key_exists('review_raw', $data);
        Log::info("Diagnostic keys product={$productKey} hasTrust=" . ($hasTrust?'Y':'N') . " hasSent=" . ($hasSent?'Y':'N') . " hasRaw=" . ($hasRaw?'Y':'N') . " types trust=" . gettype($data['trust'] ?? null) . " sentiment=" . gettype($data['sentiment'] ?? null) . " review_raw=" . gettype($data['review_raw'] ?? null));
        if ($hasTrust && is_array($data['trust']) && count($data['trust'])>0) {
            $sampleT = $data['trust'][0];
            Log::info("Sample trust row keys=" . (is_array($sampleT)? implode(',', array_keys($sampleT)) : 'non-array'));
        }
        if ($hasSent && is_array($data['sentiment']) && count($data['sentiment'])>0) {
            $sampleS = $data['sentiment'][0];
            Log::info("Sample sentiment row keys=" . (is_array($sampleS)? implode(',', array_keys($sampleS)) : 'non-array'));
        }
        if ($hasRaw && is_array($data['review_raw']) && count($data['review_raw'])>0) {
            $sampleR = $data['review_raw'][0];
            Log::info("Sample review_raw row keys=" . (is_array($sampleR)? implode(',', array_keys($sampleR)) : 'non-array'));
        }
        $sizes = [
            'trust' => is_array($data['trust'] ?? null) ? count($data['trust']) : 0,
            'sentiment' => is_array($data['sentiment'] ?? null) ? count($data['sentiment']) : 0,
            'review_raw' => is_array($data['review_raw'] ?? null) ? count($data['review_raw']) : 0,
        ];
        Log::info("Flask dataset sizes product={$productKey} trust={$sizes['trust']} sentiment={$sizes['sentiment']} review_raw={$sizes['review_raw']} raw_keys=" . implode(',', array_keys($data)) );
        // Remove the hard abort; proceed with any non-empty source
        if ($sizes['trust'] === 0 && $sizes['sentiment'] === 0 && $sizes['review_raw'] === 0) {
            Log::warning("Empty dataset for product {$productKey}; skipping insert");
            return response()->json(['ok'=>true,'inserted'=>0,'warning'=>'empty dataset from Flask'],200);
        }

        $inserted = 0;
        DB::transaction(function () use ($productKey, $data, $force, &$inserted, $userId) {
            if ($force) {
                Comment::where('product_key', $productKey)->delete();
                Product::where('product_key', $productKey)->delete();
            }
            $pt = $data['product_trust'] ?? [];
            $summary = $data['summary'] ?? [];
            $prodName = $pt['product']['name'] ?? null;
            $metrics = $pt['metrics'] ?? [];

            $product = Product::updateOrCreate(
                ['product_key' => $productKey],
                [
                    'user_id' => $userId,
                    'shopid' => (int)explode('-', $productKey)[0],
                    'itemid' => (int)explode('-', $productKey)[1],
                    'name' => $prodName,
                    'count_reviews' => $metrics['count_reviews'] ?? 0,
                    'avg_rating' => $metrics['avg_rating'] ?? null,
                    'avg_trust_score' => $metrics['avg_trust_score'] ?? null,
                    'fake_rate' => $metrics['fake_rate'] ?? null,
                    'positive_summary' => $summary['positive_summary'] ?? null,
                    'negative_summary' => $summary['negative_summary'] ?? null,
                    'pros' => $summary['pros'] ?? [],
                    'cons' => $summary['cons'] ?? [],
                    'meta' => $pt,
                ]
            );
            // Prefer most enriched rows; fallback to sentiment then raw
            $rows = $data['trust'] ?? null;
            $source = 'trust';
            if (!$rows || (is_array($rows) && count($rows) === 0)) {
                $rows = $data['sentiment'] ?? null; $source = 'sentiment';
            }
            if (!$rows || (is_array($rows) && count($rows) === 0)) {
                $rows = $data['review_raw'] ?? []; $source = 'review_raw';
            }
            Log::info("Selected source {$source} with count=" . (is_array($rows)?count($rows):0));
            if (is_array($rows) && count($rows) > 0) {
                // log a sample row keys for debugging structure mismatch
                $sample = $rows[0];
                if (is_array($sample)) {
                    Log::info("Sample row keys (source={$source}): " . implode(',', array_keys($sample)));
                }
            }
            $now = Carbon::now();
            $buffer = [];
            foreach (($rows ?? []) as $r) {
                // Normalize keys from different sources
                $username = $r['username'] ?? $r['user'] ?? null;
                $rating = $r['rating'] ?? $r['rating_score'] ?? null;
                $comment = $r['comment'] ?? $r['content'] ?? $r['text'] ?? null;
                $likes = $r['likes'] ?? $r['like_count'] ?? 0;
                $createTime = $r['create_time'] ?? $r['ctime'] ?? null;
                $sentiment = $r['sentiment'] ?? null;
                $sentConf = $r['sentiment_confidence'] ?? $r['sent_conf'] ?? null;
                $fakePred = isset($r['fake_pred']) ? (bool)$r['fake_pred'] : (isset($r['suspicious']) ? (bool)$r['suspicious'] : false);
                $fakeScore = $r['fake_score'] ?? $r['suspicion_score'] ?? null;
                $trustScore = $r['trust_score'] ?? null;
                $textLen = $r['text_len'] ?? (is_string($comment) ? strlen($comment) : null);
                $charRep = $r['char_repeat_ratio'] ?? null;
                $tokRep = $r['token_repeat_ratio'] ?? null;
                $dup = $r['dup_score'] ?? null;
                $mismatch = isset($r['mismatch']) ? (bool)$r['mismatch'] : null;
                $productLabel = $r['product_label'] ?? null;
                $variantName = $r['variant_name'] ?? null;
                $tags = $r['tags'] ?? null; // Expect Flask to send array of tag strings per comment
                $buffer[] = [
                    'user_id' => $userId,
                    'product_id' => $product->id,
                    'product_key' => $productKey,
                    'username' => $username,
                    'comment' => $comment,
                    'rating' => $rating,
                    'likes' => $likes,
                    'create_time' => $createTime,
                    'commented_at' => null,
                    'comment_clean' => $r['comment_clean'] ?? null,
                    'tokens' => $r['tokens'] ?? null,
                    'tokens_count' => $r['tokens_count'] ?? null,
                    'sentiment' => $sentiment,
                    'sentiment_confidence' => $sentConf,
                    'fake_pred' => $fakePred,
                    'fake_score' => $fakeScore,
                    'trust_score' => $trustScore,
                    'text_len' => $textLen,
                    'char_repeat_ratio' => $charRep,
                    'token_repeat_ratio' => $tokRep,
                    'dup_score' => $dup,
                    'mismatch' => $mismatch,
                    'product_label' => $productLabel,
                    'variant_name' => $variantName,
                    'tags' => $tags,
                    'extras' => null,
                    'created_at' => $now,
                    'updated_at' => $now,
                ];
                if (count($buffer) >= 1000) {
                    Comment::insert($buffer);
                    $inserted += 1000;
                    $buffer = [];
                }
            }
            if (!empty($buffer)) {
                Comment::insert($buffer);
                $inserted += count($buffer);
            }
            Log::info("Ingested {$inserted} comments from source={$source} for product={$productKey}");
        });

        return response()->json(['ok' => true, 'inserted' => $inserted, 'product_id' => $productKey]);
    }

    public function analysisJson(string $productKey)
    {
        $p = Product::where('product_key', $productKey)->first();
        if (!$p) return response()->json(['error' => 'not found'], 404);
        $count = (int)Comment::where('product_key', $productKey)->count();
        $avgRating = (float)Comment::where('product_key', $productKey)->avg('rating');
        $avgTrust = (float)Comment::where('product_key', $productKey)->avg('trust_score');
        $fakeRate = (float)Comment::where('product_key', $productKey)->where('fake_pred', true)->count();
        $fakeRate = $count ? $fakeRate / $count : 0.0;
        // sentiment counts
        $sentCounts = Comment::select('sentiment', DB::raw('COUNT(*) as c'))
            ->where('product_key', $productKey)
            ->groupBy('sentiment')->pluck('c','sentiment')->toArray();
        // trust histogram buckets 0-100 by 10
        $bins = array_fill(0, 10, 0);
        Comment::where('product_key', $productKey)->select('trust_score')->chunk(1000, function($chunk) use (&$bins) {
            foreach ($chunk as $row) {
                $v = max(0, min(100, (float)$row->trust_score));
                $i = min(9, (int)floor($v/10));
                $bins[$i]++;
            }
        });
        // fake score histogram
        $edges = range(0, 10); // 0..10 -> /10 later
        $labels = [];$counts=[];$colors=[]; $thr=0.6;
        for ($i=0;$i<10;$i++){ $labels[] = sprintf('%.1f-%.1f', $i/10, ($i+1)/10); $counts[] = 0; }
        Comment::where('product_key', $productKey)->select('fake_score')->chunk(1000, function($chunk) use (&$counts){
            foreach ($chunk as $row) {
                $v = max(0, min(1, (float)$row->fake_score));
                $i = min(9, (int)floor($v*10));
                $counts[$i]++;
            }
        });
        for ($i=0;$i<10;$i++){ $mid = ($i+0.5)/10; $colors[] = $mid >= $thr ? '#d62728' : '#59a14f'; }

        $avgTrustNorm = $this->normalizeTrust($avgTrust);
        return response()->json([
            'product_id' => $productKey,
            'metrics' => [
                'count_reviews' => $count,
                'avg_rating' => round($avgRating,2),
                'avg_trust_score' => round($avgTrust,2),
                'avg_trust_percent_norm' => $avgTrustNorm,
                'trust_level' => $this->trustLevel($avgTrustNorm)['text'],
                'trust_level_class' => $this->trustLevel($avgTrustNorm)['class'],
                'fake_rate' => round($fakeRate,4),
                'sentiment_counts' => $sentCounts,
                'trust_hist' => $bins,
                'fake_score_hist' => [ 'bins'=>$labels, 'counts'=>$counts, 'colors'=>$colors, 'threshold'=>$thr ],
                'pros' => $p->pros ?? [],
                'cons' => $p->cons ?? [],
                'positive_summary' => $p->positive_summary ?? '',
                'negative_summary' => $p->negative_summary ?? '',
            ],
            'updated_at' => now()->toIso8601String(),
        ]);
    }

    public function analysisPage(string $productKey)
    {
        return view('analysis', ['productKey' => $productKey]);
    }

    public function productsLatest(Request $request)
    {
        $limit = (int)($request->query('limit', 10));
        $limit = max(1, min(50, $limit));
        $rows = Product::orderByDesc('updated_at')
            ->limit($limit)
            ->get(['product_key','name','avg_rating','avg_trust_score','count_reviews','fake_rate','updated_at']);
        return response()->json([
            'data' => $rows,
            'count' => $rows->count(),
        ]);
    }

    public function commentsForProduct(Request $request, string $productKey)
    {
        $limit = (int)($request->query('limit', 20));
        $limit = max(1, min(200, $limit));
        $tagFilter = $request->query('tag');
        $queryBuilder = Comment::where('product_key', $productKey);
        if ($tagFilter) {
            // Filter comments that contain the given tag in JSON array
            $queryBuilder->whereJsonContains('tags', $tagFilter);
        }
        $query = $queryBuilder
            ->orderByDesc('create_time')
            ->orderByDesc('id')
            ->limit($limit)
            ->get(['username','comment','rating','likes','sentiment','fake_pred','fake_score','trust_score','create_time','variant_name','tags']);
        return response()->json([
            'product_id' => $productKey,
            'data' => $query,
            'count' => $query->count(),
            'filter_tag' => $tagFilter,
        ]);
    }

    public function tagsForProduct(string $productKey)
    {
        // Aggregate tag frequencies across comments
        $counts = [];
        Comment::where('product_key', $productKey)->select('tags')->chunk(500, function($chunk) use (&$counts) {
            foreach ($chunk as $row) {
                $tags = $row->tags ?? [];
                if (is_array($tags)) {
                    foreach ($tags as $t) {
                        if (!is_string($t) || $t === '') continue;
                        $counts[$t] = ($counts[$t] ?? 0) + 1;
                    }
                }
            }
        });
        arsort($counts);
        $list = [];
        foreach ($counts as $tag => $c) {
            $list[] = ['tag' => $tag, 'count' => $c];
        }
        return response()->json([
            'product_id' => $productKey,
            'tags' => $list,
            'count' => count($list),
        ]);
    }

    private function normalizeTrust($v): float
    {
        $v = max(0.0, min(100.0, (float)$v));
        $z = ($v - 50.0)/10.0;
        return round(100.0/(1.0+exp(-$z)), 2);
    }
    private function trustLevel($p): array
    {
        if ($p >= 71.0) return ['text'=>'High', 'class'=>'trust-high'];
        if ($p >= 41.0) return ['text'=>'Medium', 'class'=>'trust-med'];
        return ['text'=>'Low', 'class'=>'trust-low'];
    }
}
