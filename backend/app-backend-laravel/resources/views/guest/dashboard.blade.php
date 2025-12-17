@extends('layouts.app')

@section('title', 'Dashboard - CommentTrust')

@section('content')
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Welcome Section -->
    <div class="grid md:grid-cols-3 gap-6 mb-8">
        <!-- User Info Card -->
        <div class="md:col-span-1 bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-bold text-gray-900 mb-4">👤 Your Profile</h2>
            <div class="space-y-3">
                <div>
                    <p class="text-xs text-gray-600 uppercase tracking-wide">Name</p>
                    <p class="text-lg font-semibold text-gray-900">{{ Auth::user()->name }}</p>
                </div>
                <div>
                    <p class="text-xs text-gray-600 uppercase tracking-wide">Email</p>
                    <p class="text-sm text-gray-700">{{ Auth::user()->email }}</p>
                </div>
                <div>
                    <p class="text-xs text-gray-600 uppercase tracking-wide">Account Type</p>
                    @if (Auth::user()->is_guest)
                        <span class="inline-block px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full">
                            🚀 Guest User
                        </span>
                    @else
                        <span class="inline-block px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full">
                            ⭐ Premium User
                        </span>
                    @endif
                </div>
                <a href="{{ route('profile') }}" class="inline-block mt-4 text-indigo-600 hover:underline text-sm font-medium">
                    Edit Profile →
                </a>
            </div>
        </div>

        <!-- Guest Token Status (Only for Guests) -->
        @if (Auth::user()->is_guest && Auth::user()->token_expires_at)
            <div class="md:col-span-1 bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
                <h2 class="text-lg font-bold text-gray-900 mb-4">⏱️ Token Status</h2>
                <div class="space-y-3">
                    @php
                        $expiresAt = Auth::user()->token_expires_at;
                        $now = now();
                        $secondsRemaining = $expiresAt->diffInSeconds($now);
                        $hoursRemaining = floor($secondsRemaining / 3600);
                        $minutesRemaining = floor(($secondsRemaining % 3600) / 60);
                        $isExpiringSoon = $secondsRemaining < (6 * 3600); // Less than 6 hours
                    @endphp

                    <div>
                        <p class="text-xs text-gray-600 uppercase tracking-wide">Expires At</p>
                        <p class="text-sm font-mono text-gray-700">
                            {{ $expiresAt->format('M d, Y H:i A') }}
                        </p>
                    </div>

                    <div>
                        <p class="text-xs text-gray-600 uppercase tracking-wide">Time Remaining</p>
                        <div class="flex items-baseline gap-2 mt-1">
                            <p class="text-lg font-bold {{ $isExpiringSoon ? 'text-orange-600' : 'text-green-600' }}">
                                {{ $hoursRemaining }}h {{ $minutesRemaining }}m
                            </p>
                            @if ($isExpiringSoon)
                                <span class="text-xs text-orange-600 font-semibold">⚠️ Expiring soon!</span>
                            @endif
                        </div>
                    </div>

                    <!-- Token Progress Bar -->
                    @php
                        $totalSeconds = Auth::user()->created_at->diffInSeconds(Auth::user()->token_expires_at);
                        $progressPercent = max(0, min(100, ($secondsRemaining / $totalSeconds) * 100));
                    @endphp
                    <div class="mt-4">
                        <div class="w-full bg-gray-200 rounded-full h-2">
                            <div 
                                class="h-2 rounded-full transition-all {{ $isExpiringSoon ? 'bg-orange-500' : 'bg-green-500' }}"
                                style="width: {{ $progressPercent }}%"
                            ></div>
                        </div>
                    </div>

                    <!-- Refresh Token Button -->
                    <form method="POST" action="{{ route('guest.refresh-token') }}" class="mt-4">
                        @csrf
                        <button 
                            type="submit"
                            class="w-full bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition duration-200 text-sm"
                        >
                            🔄 Refresh Token (24h more)
                        </button>
                    </form>

                    <!-- Convert to Regular User -->
                    <a 
                        href="{{ route('convert-to-user') }}"
                        class="block w-full text-center bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 transition duration-200 text-sm mt-2"
                    >
                        ⭐ Upgrade to Regular Account
                    </a>
                </div>
            </div>
        @else
            <!-- Regular User Info -->
            <div class="md:col-span-1 bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
                <h2 class="text-lg font-bold text-gray-900 mb-4">⭐ Premium Features</h2>
                <ul class="space-y-2 text-sm text-gray-700">
                    <li class="flex items-center gap-2">
                        <span class="text-green-500">✓</span>
                        Unlimited analysis
                    </li>
                    <li class="flex items-center gap-2">
                        <span class="text-green-500">✓</span>
                        Advanced reporting
                    </li>
                    <li class="flex items-center gap-2">
                        <span class="text-green-500">✓</span>
                        Email support
                    </li>
                    <li class="flex items-center gap-2">
                        <span class="text-green-500">✓</span>
                        API access
                    </li>
                </ul>
                <p class="text-xs text-gray-500 mt-4">
                    Your account has no token expiration.
                </p>
            </div>
        @endif

        <!-- Quick Stats -->
        <div class="md:col-span-1 bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-bold text-gray-900 mb-4">📊 Statistics</h2>
            <div class="space-y-3">
                <div>
                    <p class="text-xs text-gray-600 uppercase tracking-wide">Products Analyzed</p>
                    <p class="text-2xl font-bold text-indigo-600">{{ $productCount ?? 0 }}</p>
                </div>
                <div>
                    <p class="text-xs text-gray-600 uppercase tracking-wide">Comments Processed</p>
                    <p class="text-2xl font-bold text-indigo-600">{{ $commentCount ?? 0 }}</p>
                </div>
                <div>
                    <p class="text-xs text-gray-600 uppercase tracking-wide">Member Since</p>
                    <p class="text-sm font-mono text-gray-700">
                        {{ Auth::user()->created_at->format('M d, Y') }}
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- Scrape New Product Section -->
    <div class="bg-gradient-to-r from-indigo-600 to-blue-600 rounded-lg shadow-lg p-6 mb-8">
        <h2 class="text-xl font-bold text-white mb-4">🔍 Scrape New Product</h2>
        <p class="text-indigo-100 text-sm mb-4">Enter a Shopee or Tokopedia product URL to start scraping and analysis</p>
        
        <form id="scrapeForm" class="flex gap-3">
            <input 
                type="url" 
                id="productUrl" 
                placeholder="https://shopee.co.id/product/..." 
                required
                class="flex-1 px-4 py-3 rounded-lg border-0 focus:ring-2 focus:ring-white"
            >
            <button 
                type="submit"
                class="bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold hover:bg-indigo-50 transition whitespace-nowrap"
            >
                🚀 Start Scraping
            </button>
        </form>

        <div id="scrapeStatus" class="mt-4 hidden">
            <div class="bg-white rounded-lg p-4">
                <p id="statusMessage" class="text-sm text-gray-700"></p>
                <div id="progressBar" class="w-full bg-gray-200 rounded-full h-2 mt-2 hidden">
                    <div class="bg-indigo-600 h-2 rounded-full transition-all" style="width: 0%" id="progress"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Products Section -->
    <div class="bg-white rounded-lg shadow">
        <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 class="text-xl font-bold text-gray-900">📦 Your Products</h2>
            <button onclick="location.reload()" class="text-indigo-600 hover:text-indigo-700 text-sm font-medium">
                🔄 Refresh
            </button>
        </div>

        @if (isset($products) && count($products) > 0)
            <div class="divide-y divide-gray-200">
                @foreach ($products as $product)
                    <div class="px-6 py-4 hover:bg-gray-50 transition">
                        <div class="flex justify-between items-start">
                            <div>
                                <h3 class="font-semibold text-gray-900">{{ $product->name }}</h3>
                                <p class="text-sm text-gray-600 mt-1">{{ Str::limit($product->description, 100) }}</p>
                                <p class="text-xs text-gray-500 mt-2">
                                    Added {{ $product->created_at->diffForHumans() }}
                                </p>
                            </div>
                            <a 
                                href="#" 
                                class="text-indigo-600 hover:text-indigo-700 font-medium text-sm whitespace-nowrap ml-4"
                            >
                                View Details →
                            </a>
                        </div>
                    </div>
                @endforeach
            </div>
        @else
            <div class="px-6 py-12 text-center">
                <p class="text-gray-500 text-sm">No products yet.</p>
                <a href="#" class="text-indigo-600 hover:underline mt-2 inline-block text-sm font-medium">
                    Start analyzing a product
                </a>
            </div>
        @endif
    </div>

    <!-- API Token Display (Optional - for development) -->
    <div class="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h3 class="font-bold text-yellow-900 mb-2">🔐 API Token (for Development)</h3>
        <p class="text-xs text-yellow-700 mb-3">
            Use this token in API requests. Keep it secret!
        </p>
        <div class="bg-white p-3 rounded border border-yellow-300 font-mono text-xs text-gray-600 break-all">
            Bearer {{ session('api_token') ?? '(token not available in session)' }}
        </div>
        <p class="text-xs text-yellow-600 mt-2">
            📌 Save this token locally. You'll need it for API requests.
        </p>
    </div>
</div>

<script>
// Lightweight status helper
function setStatus(msg, color = 'text-gray-700') {
    const statusMessage = document.getElementById('statusMessage');
    statusMessage.className = `text-sm ${color}`;
    statusMessage.textContent = msg;
}

// Helper to perform API calls with Bearer token and auto-refresh on 401
async function apiFetch(url, options = {}) {
    let token = (typeof localStorage !== 'undefined' && localStorage.getItem('api_token')) || '{{ session('api_token') }}';
    const headers = Object.assign({
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
    }, options.headers || {});
    if (token) headers['Authorization'] = 'Bearer ' + token;
    const resp = await fetch(url, Object.assign({}, options, { headers }));
    if (resp.status === 401) {
        // Try to generate a new token, then retry once
        try {
            const genResp = await fetch('/api/auth/token/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    ...(token ? { 'Authorization': 'Bearer ' + token } : {}),
                },
                body: JSON.stringify({ reason: 'auto-refresh from dashboard' })
            });
            const genData = await genResp.json().catch(() => ({}));
            if (genResp.ok && (genData.token || genData.api_token)) {
                token = genData.token || genData.api_token;
                try { localStorage.setItem('api_token', token); } catch (e) {}
                headers['Authorization'] = 'Bearer ' + token;
                return fetch(url, Object.assign({}, options, { headers }));
            }
        } catch (e) {
            // fall through
        }

        // As guest users may not have a valid token, attempt guest login to obtain one
        try {
            const guestResp = await fetch('/api/guest/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({ purpose: 'dashboard-auto-login' })
            });
            const guestData = await guestResp.json().catch(() => ({}));
            if (guestResp.ok && (guestData.token || guestData.api_token)) {
                token = guestData.token || guestData.api_token;
                try { localStorage.setItem('api_token', token); } catch (e) {}
                headers['Authorization'] = 'Bearer ' + token;
                return fetch(url, Object.assign({}, options, { headers }));
            }
        } catch (e) {
            // fall through
        }
    }
    return resp;
}

// Wait until scrape-only job finishes before requesting analysis
async function waitForScrapeCompletion(jobId, productIdHint) {
    const maxMs = 12 * 60 * 1000; // 12 minutes cap
    const delay = (ms) => new Promise(res => setTimeout(res, ms));
    const start = Date.now();
    let productId = productIdHint;
    while (Date.now() - start < maxMs) {
        setStatus('🧭 Menunggu scraping selesai... (job ' + jobId + ')', 'text-gray-700');
        const resp = await apiFetch(`/api/analysis/job/${encodeURIComponent(jobId)}`);
        const data = await resp.json().catch(() => ({}));
        const job = (data && (data.job?.data || data.job || data.data)) || {};
        if (job.product_id && !productId) productId = job.product_id;

        const phase = job.phase || 'unknown';
        const scrTotal = Number(job.scraper_total || 0);
        const scrProg = Number(job.scraper_progress || 0);
        if (phase === 'error' || job.error) {
            return { ok: false, error: job.error || 'scrape error', productId };
        }
        const scrapeDone = phase === 'done' || (scrTotal > 0 && scrProg >= scrTotal);
        if (scrapeDone) {
            return { ok: true, productId: productId || job.product_id }; // proceed
        }
        await delay(4000);
    }
    return { ok: false, error: 'timeout menunggu scraping selesai', productId };
}

document.getElementById('scrapeForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const productUrl = document.getElementById('productUrl').value;
    const statusDiv = document.getElementById('scrapeStatus');
    const statusMessage = document.getElementById('statusMessage');
    const progressBar = document.getElementById('progressBar');
    const progress = document.getElementById('progress');
    
    // Show status
    statusDiv.classList.remove('hidden');
    setStatus('⏳ Menyiapkan permintaan scraping...', 'text-gray-700');
    progressBar.classList.remove('hidden');
    progress.style.width = '20%';
    
    try {
        setStatus('🔑 Memeriksa token & autentikasi...', 'text-gray-700');
        // Call analysis scrape endpoint defined in api.php
        const response = await apiFetch('/api/analysis/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            // Send canonical key expected by controller
            body: JSON.stringify({ product_url: productUrl, source: 'shopee' })
        });
        setStatus('⏳ Mengirim permintaan ke scraper...', 'text-gray-700');
        const data = await response.json();
        progress.style.width = '100%';
        
        if (data.ok || response.ok) {
            let productId = data.product_id || data.id || (data.product && data.product.id) || null;
            setStatus('✅ Permintaan scraping dikirim. Backend sedang berjalan.' + (productId ? ' Product ID: ' + productId : ''), 'text-green-700');
            
            // Show job info if available
            if (data.job_id) {
                const jobInfo = document.createElement('div');
                jobInfo.className = 'mt-2 text-xs text-gray-600 bg-green-50 rounded p-2';
                jobInfo.textContent = 'Job ID: ' + data.job_id + ' — proses berjalan di backend.';
                statusMessage.parentElement.appendChild(jobInfo);
            }

            // Wait for scraping to finish before firing analysis
            if (data.job_id) {
                const waitRes = await waitForScrapeCompletion(data.job_id, productId);
                if (!waitRes.ok) {
                    setStatus('⚠️ Scraping belum selesai: ' + (waitRes.error || 'unknown'), 'text-orange-600');
                    return;
                }
                productId = waitRes.productId;
            }

            // Trigger analysis only after scrape completion
            if (productId) {
                setStatus('⏳ Memulai analisis komentar setelah scraping selesai...', 'text-gray-700');
                const analyzeResp = await apiFetch(`/api/analysis/analyze/${productId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({})
                });
                const analyzeData = await analyzeResp.json().catch(() => ({}));
                if (analyzeData.ok || analyzeResp.ok) {
                    const analyzeJob = analyzeData.job_id || 'N/A';
                    setStatus('✅ Permintaan analisis dikirim setelah scraping selesai. Job ID: ' + analyzeJob, 'text-green-700');
                    const jobInfo2 = document.createElement('div');
                    jobInfo2.className = 'mt-2 text-xs text-gray-600 bg-green-50 rounded p-2';
                    jobInfo2.textContent = 'Analysis job berjalan di backend. Anda bisa me-refresh daftar produk untuk melihat hasil.';
                    statusMessage.parentElement.appendChild(jobInfo2);
                } else {
                    const errTxt = (analyzeData && (analyzeData.message || analyzeData.error)) || 'Gagal memulai analisis';
                    setStatus('⚠️ Analisis gagal dimulai: ' + errTxt, 'text-orange-600');
                }
            } else {
                setStatus('✅ Scraping dimulai. Menunggu backend selesai sebelum analisis; Product ID belum tersedia.', 'text-green-700');
            }
        } else {
            const errText = (data && (data.message || data.error)) || 'Failed to scrape product';
            setStatus('❌ Error (' + response.status + '): ' + errText, 'text-red-700');
            progress.classList.add('bg-red-600');
            if (response.status === 401) {
                const help = 'Your API token may be missing or expired. Please refresh your token from the profile or try again.';
                statusMessage.textContent += ' — ' + help;
            }
            if (data && data.details) {
                const detailsEl = document.createElement('pre');
                detailsEl.className = 'mt-2 text-xs text-gray-600 bg-gray-100 rounded p-2 overflow-auto';
                detailsEl.textContent = JSON.stringify(data.details, null, 2);
                statusMessage.parentElement.appendChild(detailsEl);
            }
        }
    } catch (error) {
        progress.style.width = '100%';
        progress.classList.add('bg-red-600');
        setStatus('❌ Error: ' + error.message, 'text-red-700');
    }
});
</script>
@endsection
