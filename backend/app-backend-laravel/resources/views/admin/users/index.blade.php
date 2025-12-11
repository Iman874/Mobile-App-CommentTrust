@extends('admin.layout')

@section('page-title', 'User Management')
@section('page-subtitle', 'Manage all non-admin users and their activities')

@section('admin-content')
<div class="bg-white rounded-lg shadow overflow-hidden">
    <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h3 class="text-lg font-semibold text-gray-900">All Users (Non-Admin)</h3>
        <div class="flex gap-2">
            <input 
                type="text" 
                id="searchInput" 
                placeholder="Search users..." 
                class="px-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
        </div>
    </div>

    <div class="overflow-x-auto">
        <table class="w-full">
            <thead class="bg-gray-50 border-b border-gray-200">
                <tr>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Name</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Email</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Products</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Token</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Expires</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Created</th>
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
                @forelse ($users as $user)
                    <tr class="hover:bg-gray-50 transition">
                        <td class="px-6 py-4">
                            <div class="flex items-center">
                                <img src="https://ui-avatars.com/api/?name={{ $user->name }}" alt="Avatar" class="w-8 h-8 rounded-full mr-3">
                                <div>
                                    <p class="text-sm font-medium text-gray-900">{{ $user->name }}</p>
                                    @if ($user->is_guest)
                                        <span class="inline-block mt-1 px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Guest</span>
                                    @else
                                        <span class="inline-block mt-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Regular</span>
                                    @endif
                                </div>
                            </div>
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-700">{{ $user->email }}</td>
                        <td class="px-6 py-4 text-sm text-gray-700">
                            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {{ $user->products->count() }}
                            </span>
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-700">
                            @if ($user->api_token)
                                <code class="bg-gray-100 px-2 py-1 rounded text-xs">{{ substr($user->api_token, 0, 12) }}...</code>
                            @else
                                <span class="text-gray-400">No token</span>
                            @endif
                        </td>
                        <td class="px-6 py-4 text-sm">
                            @if ($user->token_expires_at)
                                @if ($user->token_expires_at->isFuture())
                                    <span class="text-green-600">{{ $user->token_expires_at->format('M d, Y H:i') }}</span>
                                @else
                                    <span class="text-red-600">Expired</span>
                                @endif
                            @else
                                <span class="text-gray-400">-</span>
                            @endif
                        </td>
                        <td class="px-6 py-4 text-sm text-gray-500">{{ $user->created_at->format('M d, Y') }}</td>
                        <td class="px-6 py-4 text-sm space-x-2">
                            <a href="{{ route('admin.users.show', $user->id) }}" class="text-indigo-600 hover:text-indigo-900">View</a>
                            <button onclick="deleteUser({{ $user->id }})" class="text-red-600 hover:text-red-900">Delete</button>
                        </td>
                    </tr>
                @empty
                    <tr>
                        <td colspan="7" class="px-6 py-8 text-center text-gray-500">
                            No guest users found
                        </td>
                    </tr>
                @endforelse
            </tbody>
        </table>
    </div>

    <!-- Pagination -->
    <div class="px-6 py-4 border-t border-gray-200">
        {{ $users->links() }}
    </div>
</div>

<!-- View User Modal -->
<div id="userModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4">
        <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h3 class="text-lg font-semibold text-gray-900">User Details</h3>
            <button onclick="closeUserModal()" class="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <div id="modalContent" class="p-6">
            <!-- Content will be loaded here -->
        </div>
    </div>
</div>

<script>
function deleteUser(userId) {
    if (confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
        fetch(`/api/admin/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.ok) {
                alert('User deleted successfully');
                location.reload();
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

function closeUserModal() {
    document.getElementById('userModal').classList.add('hidden');
}

document.getElementById('searchInput').addEventListener('keyup', function() {
    const searchTerm = this.value.toLowerCase();
    document.querySelectorAll('tbody tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
});
</script>
@endsection
