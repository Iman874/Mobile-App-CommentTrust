<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Http\Client\Response;
use Illuminate\Http\Client\RequestException;

class FlaskService
{
    private string $baseUrl;
    private int $timeout = 300; // 5 minutes for long-running analysis

    public function __construct()
    {
        $this->baseUrl = config('services.flask.url') ?? env('FLASK_API_URL', 'http://localhost:5000');
    }

    /**
     * Start full analysis (scrape + analyze)
     */
    public function analyzeFullUrl(string $productUrl): array
    {
        return $this->post('/api/input/link', [
            'link' => $productUrl,
            'force_copy_browser' => false
        ]);
    }

    /**
     * Get analysis job status
     */
    public function getJobStatus(string $jobId): array
    {
        return $this->get("/api/job/{$jobId}");
    }

    /**
     * Get all analysis history/products
     */
    public function getProductsHistory(): array
    {
        return $this->get('/api/history/products');
    }

    /**
     * Get product statistics
     */
    public function getProductStats(string $productId): array
    {
        return $this->get("/api/product/{$productId}/stats");
    }

    /**
     * Get comments for product with filters
     */
    public function getComments(
        string $productId,
        int $page = 1,
        int $perPage = 10,
        ?array $tags = null,
        ?string $sentiment = null,
        ?string $search = null
    ): array {
        $params = [
            'page' => $page,
            'per_page' => $perPage,
        ];

        if ($tags) {
            $params['tags'] = implode(',', $tags);
        }
        if ($sentiment) {
            $params['sentiment'] = $sentiment;
        }
        if ($search) {
            $params['search'] = $search;
        }

        return $this->get("/api/comments/{$productId}", $params);
    }

    /**
     * Re-analyze existing product
     */
    public function reanalyzeProduct(string $productId): array
    {
        return $this->post("/api/reanalyze/{$productId}", []);
    }

    /**
     * Get scrape-only job
     */
    public function scrapeOnly(string $productUrl): array
    {
        return $this->post('/api/scrape/start', [
            'link' => $productUrl
        ]);
    }

    /**
     * Get analysis-only job (from existing scraped data)
     */
    public function analyzeOnly(string $productId): array
    {
        return $this->post("/api/analyze/{$productId}", []);
    }

    /**
     * Make GET request to Flask API
     */
    private function get(string $endpoint, array $params = []): array
    {
        try {
            $response = Http::timeout($this->timeout)
                ->get($this->baseUrl . $endpoint, $params);

            return $this->handleResponse($response);
        } catch (RequestException $e) {
            return [
                'ok' => false,
                'error' => $e->getMessage(),
                'status' => $e->response?->status() ?? 500
            ];
        } catch (\Exception $e) {
            return [
                'ok' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    /**
     * Make POST request to Flask API
     */
    private function post(string $endpoint, array $data): array
    {
        try {
            $response = Http::timeout($this->timeout)
                ->post($this->baseUrl . $endpoint, $data);

            return $this->handleResponse($response);
        } catch (RequestException $e) {
            return [
                'ok' => false,
                'error' => $e->getMessage(),
                'status' => $e->response?->status() ?? 500
            ];
        } catch (\Exception $e) {
            return [
                'ok' => false,
                'error' => $e->getMessage()
            ];
        }
    }

    /**
     * Handle Flask response
     */
    private function handleResponse(Response $response): array
    {
        try {
            $json = $response->json();
            
            // If response has 'ok' field, use it; otherwise check HTTP status
            if (is_array($json) && isset($json['ok'])) {
                return $json;
            }

            // Assume success if HTTP status is 2xx
            return [
                'ok' => $response->successful(),
                'data' => $json,
                'status' => $response->status()
            ];
        } catch (\Exception $e) {
            return [
                'ok' => false,
                'error' => 'Invalid JSON response from Flask',
                'status' => $response->status()
            ];
        }
    }
}
