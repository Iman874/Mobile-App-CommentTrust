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
document.getElementById('scrapeForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const productUrl = document.getElementById('productUrl').value;
    const statusDiv = document.getElementById('scrapeStatus');
    const statusMessage = document.getElementById('statusMessage');
    const progressBar = document.getElementById('progressBar');
    const progress = document.getElementById('progress');
    
    // Show status
    statusDiv.classList.remove('hidden');
    statusMessage.textContent = '⏳ Starting scraping process...';
    progressBar.classList.remove('hidden');
    progress.style.width = '20%';
    
    try {
        const response = await fetch('/api/analysis/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {{ session("api_token") }}',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ product_url: productUrl })
        });
        
        const data = await response.json();
        progress.style.width = '100%';
        
        if (data.ok || response.ok) {
            statusMessage.textContent = '✅ Scraping completed! Product ID: ' + (data.product_id || 'N/A');
            statusMessage.classList.add('text-green-700');
            
            // Reload page after 2 seconds
            setTimeout(() => location.reload(), 2000);
        } else {
            statusMessage.textContent = '❌ Error: ' + (data.message || 'Failed to scrape product');
            statusMessage.classList.add('text-red-700');
            progress.classList.add('bg-red-600');
        }
    } catch (error) {
        progress.style.width = '100%';
        progress.classList.add('bg-red-600');
        statusMessage.textContent = '❌ Error: ' + error.message;
        statusMessage.classList.add('text-red-700');
    }
});
</script>
@endsection
