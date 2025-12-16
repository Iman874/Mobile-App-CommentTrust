@extends('admin.layout')

@section('page-title', 'User Details')
@section('page-subtitle', 'View user information and products')

@section('admin-content')
<!-- Include Notification Component -->
@include('components.notification')
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <!-- User Information -->
    <div class="lg:col-span-2">
        <div class="bg-white rounded-lg shadow overflow-hidden">
            <!-- Header -->
            <div class="bg-gradient-to-r from-indigo-600 to-blue-600 px-6 py-8">
                <div class="flex items-center gap-4">
                    <div class="w-16 h-16 bg-white rounded-full flex items-center justify-center">
                        <svg class="w-8 h-8 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"></path>
                        </svg>
                    </div>
                    <div class="text-white">
                        <h2 class="text-2xl font-bold">{{ $user->name }}</h2>
                        <p class="text-indigo-100">Guest User</p>
                    </div>
                </div>
            </div>

            <!-- User Details -->
            <div class="px-6 py-8 border-b border-gray-200">
                <h3 class="text-lg font-semibold text-gray-900 mb-6">Account Information</h3>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Email -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                        <p class="text-gray-900">{{ $user->email }}</p>
                    </div>

                    <!-- Username -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Username</label>
                        <p class="text-gray-900">{{ $user->username }}</p>
                    </div>

                    <!-- Registration Date -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Registered</label>
                        <p class="text-gray-900">{{ $user->created_at->format('d M Y, H:i') }}</p>
                    </div>

                    <!-- Last Activity -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Last Activity</label>
                        <p class="text-gray-900">{{ $user->updated_at->format('d M Y, H:i') }}</p>
                    </div>

                    <!-- API Token Status -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">API Token</label>
                        <div class="flex items-center gap-2">
                            <code class="bg-gray-100 px-3 py-1 rounded text-xs text-gray-700 max-w-xs truncate">
                                {{ substr($user->api_token, 0, 20) }}...
                            </code>
                            <button onclick="copyToken('{{ $user->api_token }}')" class="text-indigo-600 hover:text-indigo-700 text-sm font-medium">
                                Copy
                            </button>
                        </div>
                    </div>

                    <!-- Token Expiration -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Token Expires</label>
                        <div class="flex items-center gap-2">
                            <p class="text-gray-900">{{ $user->token_expires_at->format('d M Y, H:i') }}</p>
                            @if ($user->token_expires_at->isPast())
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                    Expired
                                </span>
                            @else
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                    Active
                                </span>
                            @endif
                        </div>
                    </div>
                </div>
            </div>

            <!-- User Statistics -->
            <div class="px-6 py-8">
                <h3 class="text-lg font-semibold text-gray-900 mb-6">Statistics</h3>

                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="bg-blue-50 rounded-lg p-4">
                        <p class="text-blue-600 text-sm font-medium">Products</p>
                        <p class="text-2xl font-bold text-blue-900 mt-2">{{ $productsCount }}</p>
                    </div>
                    <div class="bg-green-50 rounded-lg p-4">
                        <p class="text-green-600 text-sm font-medium">Comments</p>
                        <p class="text-2xl font-bold text-green-900 mt-2">{{ $commentsCount }}</p>
                    </div>
                    <div class="bg-purple-50 rounded-lg p-4">
                        <p class="text-purple-600 text-sm font-medium">Scraped</p>
                        <p class="text-2xl font-bold text-purple-900 mt-2">{{ $scrapedCount }}</p>
                    </div>
                    <div class="bg-orange-50 rounded-lg p-4">
                        <p class="text-orange-600 text-sm font-medium">Analyzed</p>
                        <p class="text-2xl font-bold text-orange-900 mt-2">{{ $analyzedCount }}</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Actions Panel -->
    <div class="lg:col-span-1">
        <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Actions</h3>

            <div class="space-y-3">
                <!-- Refresh Token -->
                <button onclick="refreshToken({{ $user->id }})" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-indigo-700 transition text-sm">
                    Refresh Token
                </button>

                <!-- Extend Token -->
                <button onclick="extendToken({{ $user->id }})" class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 transition text-sm">
                    Extend Token
                </button>

                <!-- Reset Sessions -->
                <button onclick="resetSessions({{ $user->id }})" class="w-full bg-yellow-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-yellow-700 transition text-sm">
                    Reset Sessions
                </button>

                <!-- Delete User -->
                <button onclick="deleteUser({{ $user->id }})" class="w-full bg-red-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-red-700 transition text-sm">
                    Delete User
                </button>
            </div>
        </div>

        <!-- Quick Info -->
        <div class="mt-6 bg-blue-50 rounded-lg p-6 border border-blue-200">
            <h4 class="font-semibold text-blue-900 mb-3">Quick Info</h4>
            <ul class="space-y-2 text-sm text-blue-800">
                <li class="flex items-center gap-2">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg>
                    Guest user account
                </li>
                <li class="flex items-center gap-2">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg>
                    API access enabled
                </li>
                <li class="flex items-center gap-2">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path></svg>
                    No admin access
                </li>
            </ul>
        </div>
    </div>
</div>

<!-- Products Table -->
<div class="mt-6 bg-white rounded-lg shadow overflow-hidden">
    <div class="px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">Products Scraped by User</h3>
    </div>

    @if ($products->count() > 0)
        <div class="overflow-x-auto">
            <table class="w-full">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Product</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">URL</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Comments</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Scraped</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                    @foreach ($products as $product)
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-4 text-sm font-medium text-gray-900">{{ $product->name }}</td>
                            <td class="px-6 py-4 text-sm text-gray-600">
                                <a href="{{ $product->url }}" target="_blank" class="text-indigo-600 hover:text-indigo-700 truncate max-w-xs">
                                    {{ substr($product->url, 0, 40) }}...
                                </a>
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-900">{{ $product->comments_count ?? 0 }}</td>
                            <td class="px-6 py-4 text-sm">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {{ $product->comments_count > 0 ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800' }}">
                                    {{ $product->comments_count > 0 ? 'Analyzed' : 'Pending' }}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-500">{{ $product->created_at->format('d M Y') }}</td>
                        </tr>
                    @endforeach
                </tbody>
            </table>
        </div>
    @else
        <div class="px-6 py-12 text-center text-gray-500">
            <p>No products scraped by this user yet</p>
        </div>
    @endif
</div>

<script>
function copyToken(token) {
    navigator.clipboard.writeText(token);
    notificationSystem.success('Token copied to clipboard!');
}

function refreshToken(userId) {
    if (!confirm('Are you sure you want to refresh this user\'s token?')) return;

    fetch(`/admin/users/${userId}/refresh-token`, {
        method: 'POST',
        headers: {
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
            'Content-Type': 'application/json'
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            notificationSystem.success('Token refreshed successfully. Reloading...');
            setTimeout(() => location.reload(), 1500);
        } else {
            notificationSystem.error(data.message || 'Failed to refresh token', data.code || 'UNKNOWN', 7000);
        }
    })
    .catch(error => {
        notificationSystem.error('Network error: ' + error.message, 'NETWORK_ERROR', 7000);
    });
}

function extendToken(userId) {
    if (!confirm('Are you sure you want to extend this user\'s token?')) return;

    fetch(`/admin/users/${userId}/extend-token`, {
        method: 'POST',
        headers: {
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
            'Content-Type': 'application/json'
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            notificationSystem.success('Token extended successfully. Reloading...');
            setTimeout(() => location.reload(), 1500);
        } else {
            notificationSystem.error(data.message || 'Failed to extend token', data.code || 'UNKNOWN', 7000);
        }
    })
    .catch(error => {
        notificationSystem.error('Network error: ' + error.message, 'NETWORK_ERROR', 7000);
    });
}

function resetSessions(userId) {
    if (!confirm('Are you sure you want to reset all sessions for this user?')) return;

    fetch(`/admin/users/${userId}/reset-sessions`, {
        method: 'POST',
        headers: {
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
            'Content-Type': 'application/json'
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            notificationSystem.success('Sessions reset successfully. Reloading...');
            setTimeout(() => location.reload(), 1500);
        } else {
            notificationSystem.error(data.message || 'Failed to reset sessions', data.code || 'UNKNOWN', 7000);
        }
    })
    .catch(error => {
        notificationSystem.error('Network error: ' + error.message, 'NETWORK_ERROR', 7000);
    });
}

function deleteUser(userId) {
    if (!confirm('Are you sure you want to DELETE this user? This action cannot be undone.')) return;
    if (!confirm('This will permanently delete the user account. Are you absolutely sure?')) return;

    fetch(`/admin/users/${userId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
            'Content-Type': 'application/json'
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            notificationSystem.success('User deleted successfully. Redirecting...');
            setTimeout(() => {
                window.location.href = '{{ route("admin.users") }}';
            }, 1500);
        } else {
            notificationSystem.error(data.message || 'Failed to delete user', data.code || 'UNKNOWN', 7000);
        }
    })
    .catch(error => {
        notificationSystem.error('Network error: ' + error.message, 'NETWORK_ERROR', 7000);
    });
}
</script>
@endsection
