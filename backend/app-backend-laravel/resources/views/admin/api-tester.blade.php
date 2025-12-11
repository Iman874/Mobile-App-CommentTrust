@extends('admin.layout')

@section('page-title', 'API Tester')
@section('page-subtitle', 'Test scraping, analysis and other API endpoints')

@section('admin-content')
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- Request Panel -->
    <div class="lg:col-span-2">
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">API Request</h3>

            <div class="space-y-4">
                <!-- API Endpoint Selection -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Select Endpoint</label>
                    <select id="apiEndpoint" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500">
                        <option value="">-- Choose an endpoint --</option>
                        <optgroup label="Scraping">
                            <option value="scrape">POST /api/analysis/scrape</option>
                        </optgroup>
                        <optgroup label="Analysis">
                            <option value="analyze">POST /api/analysis/analyze/{productId}</option>
                            <option value="reanalyze">POST /api/analysis/reanalyze/{productId}</option>
                        </optgroup>
                        <optgroup label="Products">
                            <option value="products">GET /api/products</option>
                        </optgroup>
                    </select>
                </div>

                <!-- Product Selection (for analysis) -->
                <div id="productSelectionDiv" class="hidden">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Select Product</label>
                    <select id="productSelect" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500">
                        <option value="">-- Loading products --</option>
                    </select>
                </div>

                <!-- URL Input (for scraping) -->
                <div id="urlInputDiv" class="hidden">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Product URL</label>
                    <input type="text" id="productUrl" placeholder="https://tokopedia.com/product/..." class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500">
                </div>

                <!-- Request Method Display -->
                <div class="bg-gray-50 p-4 rounded-lg">
                    <p class="text-sm text-gray-600">
                        <strong id="methodDisplay">GET</strong> <span id="urlDisplay">/api/products</span>
                    </p>
                </div>

                <!-- Execute Button -->
                <button onclick="executeRequest()" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-indigo-700 transition">
                    Execute Request
                </button>
            </div>
        </div>
    </div>

    <!-- Response Panel -->
    <div>
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Response</h3>

            <div id="responseContainer" class="hidden bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                <pre id="responseContent" class="text-xs text-gray-900 whitespace-pre-wrap break-words"></pre>
            </div>

            <div id="loadingSpinner" class="hidden text-center py-8">
                <div class="inline-flex items-center gap-2">
                    <div class="animate-spin h-5 w-5 text-indigo-600"></div>
                    <span class="text-gray-600">Executing request...</span>
                </div>
            </div>

            <div id="noResponseMessage" class="text-center py-8 text-gray-500">
                Response will appear here
            </div>
        </div>
    </div>
</div>

<!-- Recent Tests -->
<div class="mt-6 bg-white rounded-lg shadow overflow-hidden">
    <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">Recent API Tests</h3>
    </div>
    <div class="overflow-x-auto">
        <table class="w-full">
            <thead class="bg-gray-50">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Endpoint</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Response Time</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Tested At</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
                @forelse ($recentTests as $test)
                    <tr class="hover:bg-gray-50">
                        <td class="px-6 py-4 text-sm text-gray-900">{{ $test['endpoint'] }}</td>
                        <td class="px-6 py-4 text-sm">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {{ $test['status'] == 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800' }}">
                                {{ ucfirst($test['status']) }}
                            </span>
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-600">{{ $test['response_time'] }}ms</td>
                        <td class="px-6 py-4 text-sm text-gray-500">{{ $test['tested_at'] }}</td>
                    </tr>
                @empty
                    <tr>
                        <td colspan="4" class="px-6 py-8 text-center text-gray-500">
                            No tests yet
                        </td>
                    </tr>
                @endforelse
            </tbody>
        </table>
    </div>
</div>

<script>
let selectedEndpoint = '';

document.getElementById('apiEndpoint').addEventListener('change', function() {
    selectedEndpoint = this.value;
    updateUI();
});

function updateUI() {
    document.getElementById('urlInputDiv').classList.add('hidden');
    document.getElementById('productSelectionDiv').classList.add('hidden');

    if (selectedEndpoint === 'scrape') {
        document.getElementById('urlInputDiv').classList.remove('hidden');
        document.getElementById('methodDisplay').textContent = 'POST';
        document.getElementById('urlDisplay').textContent = '/api/analysis/scrape';
    } else if (selectedEndpoint.includes('analyze')) {
        document.getElementById('productSelectionDiv').classList.remove('hidden');
        loadProducts();
        document.getElementById('methodDisplay').textContent = 'POST';
        document.getElementById('urlDisplay').textContent = `/api/analysis/${selectedEndpoint}/{productId}`;
    } else if (selectedEndpoint === 'products') {
        document.getElementById('methodDisplay').textContent = 'GET';
        document.getElementById('urlDisplay').textContent = '/api/products';
    }
}

function loadProducts() {
    fetch('/api/admin/products', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(r => r.json())
    .then(data => {
        const select = document.getElementById('productSelect');
        select.innerHTML = '<option value="">-- Select a product --</option>';
        if (data.products) {
            data.products.forEach(product => {
                const option = document.createElement('option');
                option.value = product.id;
                option.textContent = product.name;
                select.appendChild(option);
            });
        }
    });
}

function executeRequest() {
    const responseContainer = document.getElementById('responseContainer');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const noResponseMessage = document.getElementById('noResponseMessage');
    const responseContent = document.getElementById('responseContent');

    responseContainer.classList.add('hidden');
    noResponseMessage.classList.add('hidden');
    loadingSpinner.classList.remove('hidden');

    const startTime = Date.now();

    let endpoint = '';
    let method = 'GET';
    let body = null;

    if (selectedEndpoint === 'scrape') {
        const url = document.getElementById('productUrl').value;
        if (!url) {
            alert('Please enter a product URL');
            loadingSpinner.classList.add('hidden');
            return;
        }
        endpoint = '/api/analysis/scrape';
        method = 'POST';
        body = { product_url: url };
    } else if (selectedEndpoint === 'analyze') {
        const productId = document.getElementById('productSelect').value;
        if (!productId) {
            alert('Please select a product');
            loadingSpinner.classList.add('hidden');
            return;
        }
        endpoint = `/api/analysis/analyze/${productId}`;
        method = 'POST';
    } else if (selectedEndpoint === 'reanalyze') {
        const productId = document.getElementById('productSelect').value;
        if (!productId) {
            alert('Please select a product');
            loadingSpinner.classList.add('hidden');
            return;
        }
        endpoint = `/api/analysis/reanalyze/${productId}`;
        method = 'POST';
    } else if (selectedEndpoint === 'products') {
        endpoint = '/api/products';
        method = 'GET';
    }

    const options = {
        method: method,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
        }
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    fetch(endpoint, options)
        .then(r => r.json())
        .then(data => {
            const responseTime = Date.now() - startTime;
            responseContent.textContent = JSON.stringify(data, null, 2);
            responseContainer.classList.remove('hidden');
            loadingSpinner.classList.add('hidden');

            // Save test
            fetch('/api/admin/api-tests', {
                method: 'POST',
                headers: {
                    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    endpoint: endpoint,
                    status: data.ok ? 'success' : 'error',
                    response_time: responseTime
                })
            });
        })
        .catch(error => {
            const responseTime = Date.now() - startTime;
            responseContent.textContent = JSON.stringify({ error: error.message }, null, 2);
            responseContainer.classList.remove('hidden');
            loadingSpinner.classList.add('hidden');
        });
}
</script>
@endsection
