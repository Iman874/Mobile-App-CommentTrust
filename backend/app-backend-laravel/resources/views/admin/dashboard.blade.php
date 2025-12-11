@extends('admin.layout')

@section('page-title', 'Dashboard')
@section('page-subtitle', 'Welcome to CommentTrust Admin Panel')

@section('admin-content')
<!-- Scrape New Product Section -->
<div class="bg-gradient-to-r from-indigo-600 to-blue-600 rounded-lg shadow-lg p-6 mb-6">
    <h2 class="text-xl font-bold text-white mb-2">🔍 Scrape New Product</h2>
    <p class="text-indigo-100 text-sm mb-4">Enter a Shopee or Tokopedia product URL to start scraping</p>
    
    <form id="adminScrapeForm" class="flex gap-3">
        <input 
            type="url" 
            id="adminProductUrl" 
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

    <div id="adminScrapeStatus" class="mt-4 hidden">
        <div class="bg-white rounded-lg p-4">
            <p id="adminStatusMessage" class="text-sm text-gray-700"></p>
            <div id="adminProgressBar" class="w-full bg-gray-200 rounded-full h-2 mt-2 hidden">
                <div class="bg-indigo-600 h-2 rounded-full transition-all" style="width: 0%" id="adminProgress"></div>
            </div>
        </div>
    </div>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
    <!-- Total Users Card -->
    <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-gray-500 text-sm">Total Users</p>
                <p class="text-3xl font-bold text-gray-900">{{ $totalUsers }}</p>
            </div>
            <div class="bg-blue-100 p-3 rounded-lg">
                <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.856-1.487M15 10a3 3 0 11-6 0 3 3 0 016 0zM12 14a8 8 0 00-8 8v2h16v-2a8 8 0 00-8-8z"></path>
                </svg>
            </div>
        </div>
    </div>

    <!-- Guest Users Card -->
    <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-gray-500 text-sm">Guest Users</p>
                <p class="text-3xl font-bold text-green-600">{{ $guestUsers }}</p>
            </div>
            <div class="bg-green-100 p-3 rounded-lg">
                <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 10h-2m2 0h2m-2 0v2m0-2v-2m2 2h2m-2 0h-2m2 0v2m0-2v-2m-4-4H8a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V4a2 2 0 00-2-2z"></path>
                </svg>
            </div>
        </div>
    </div>

    <!-- Total Products Card -->
    <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-gray-500 text-sm">Products</p>
                <p class="text-3xl font-bold text-purple-600">{{ $totalProducts }}</p>
            </div>
            <div class="bg-purple-100 p-3 rounded-lg">
                <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"></path>
                </svg>
            </div>
        </div>
    </div>

    <!-- Total Comments Card -->
    <div class="bg-white rounded-lg shadow p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-gray-500 text-sm">Comments</p>
                <p class="text-3xl font-bold text-orange-600">{{ $totalComments }}</p>
            </div>
            <div class="bg-orange-100 p-3 rounded-lg">
                <svg class="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"></path>
                </svg>
            </div>
        </div>
    </div>
</div>

<!-- Recent Activity -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Recent Users -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200">
            <h3 class="text-lg font-semibold text-gray-900">Recent Guest Users</h3>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Name</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Created</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                    @forelse ($recentUsers as $user)
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-4 text-sm text-gray-900">{{ $user->name }}</td>
                            <td class="px-6 py-4 text-sm text-gray-500">{{ $user->created_at->diffForHumans() }}</td>
                        </tr>
                    @empty
                        <tr>
                            <td colspan="2" class="px-6 py-4 text-sm text-gray-500 text-center">No guest users yet</td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </div>

    <!-- System Status -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
        <div class="px-6 py-4 border-b border-gray-200">
            <h3 class="text-lg font-semibold text-gray-900">System Status</h3>
        </div>
        <div class="p-6 space-y-4">
            <div class="flex items-center justify-between">
                <span class="text-gray-700">Database</span>
                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    ✓ Connected
                </span>
            </div>
            <div class="flex items-center justify-between">
                <span class="text-gray-700">Laravel Queue</span>
                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    ✓ Running
                </span>
            </div>
            <div class="flex items-center justify-between">
                <span class="text-gray-700">API Status</span>
                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    ✓ Operational
                </span>
            </div>
            <div class="flex items-center justify-between">
                <span class="text-gray-700">Last Updated</span>
                <span class="text-sm text-gray-500">Just now</span>
            </div>
        </div>
    </div>
</div>

<script>
document.getElementById('adminScrapeForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const productUrl = document.getElementById('adminProductUrl').value;
    const statusDiv = document.getElementById('adminScrapeStatus');
    const statusMessage = document.getElementById('adminStatusMessage');
    const progressBar = document.getElementById('adminProgressBar');
    const progress = document.getElementById('adminProgress');
    
    statusDiv.classList.remove('hidden');
    statusMessage.textContent = '⏳ Starting scraping process...';
    progressBar.classList.remove('hidden');
    progress.style.width = '20%';
    
    try {
        const response = await fetch('/api/analysis/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer {{ Auth::user()->api_token }}',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ product_url: productUrl })
        });
        
        const data = await response.json();
        progress.style.width = '100%';
        
        if (data.ok || response.ok) {
            statusMessage.textContent = '✅ Scraping completed! Product ID: ' + (data.product_id || 'N/A');
            statusMessage.classList.add('text-green-700');
            
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
