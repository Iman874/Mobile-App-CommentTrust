@extends('layouts.app')

@section('title', 'Profile - CommentTrust')

@section('content')
<div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="bg-white rounded-lg shadow p-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-8">👤 Profile Settings</h1>

        @if ($errors->any())
            <div class="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                <p class="font-medium mb-2">Update failed:</p>
                @foreach ($errors->all() as $error)
                    <p class="text-sm">• {{ $error }}</p>
                @endforeach
            </div>
        @endif

        <form method="POST" action="{{ route('profile.update') }}" class="space-y-6">
            @csrf
            @method('PUT')

            <!-- Basic Information Section -->
            <div class="border-b border-gray-200 pb-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
                
                <div class="space-y-4">
                    <div>
                        <label for="name" class="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                        <input 
                            type="text" 
                            id="name" 
                            name="name" 
                            value="{{ old('name', Auth::user()->name) }}"
                            required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        >
                        @error('name')
                            <p class="text-red-500 text-xs mt-1">{{ $message }}</p>
                        @enderror
                    </div>

                    <div>
                        <label for="email" class="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                        <input 
                            type="email" 
                            id="email" 
                            name="email" 
                            value="{{ old('email', Auth::user()->email) }}"
                            required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        >
                        @error('email')
                            <p class="text-red-500 text-xs mt-1">{{ $message }}</p>
                        @enderror
                    </div>

                    <div class="bg-blue-50 p-3 rounded text-sm text-blue-700">
                        <p><strong>Account Type:</strong> 
                            @if (Auth::user()->is_guest)
                                🚀 Guest User
                            @else
                                ⭐ Premium User
                            @endif
                        </p>
                    </div>
                </div>
            </div>

            <!-- Password Change Section -->
            <div class="border-b border-gray-200 pb-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">Change Password</h2>
                <p class="text-sm text-gray-600 mb-4">
                    Leave blank to keep your current password.
                </p>

                <div class="space-y-4">
                    <div>
                        <label for="current_password" class="block text-sm font-medium text-gray-700 mb-2">
                            Current Password
                        </label>
                        <input 
                            type="password" 
                            id="current_password" 
                            name="current_password"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            placeholder="••••••••"
                        >
                        @error('current_password')
                            <p class="text-red-500 text-xs mt-1">{{ $message }}</p>
                        @enderror
                    </div>

                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
                            New Password
                        </label>
                        <input 
                            type="password" 
                            id="password" 
                            name="password"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            placeholder="••••••••"
                        >
                        @error('password')
                            <p class="text-red-500 text-xs mt-1">{{ $message }}</p>
                        @enderror
                        <p class="text-xs text-gray-500 mt-1">At least 8 characters</p>
                    </div>

                    <div>
                        <label for="password_confirmation" class="block text-sm font-medium text-gray-700 mb-2">
                            Confirm New Password
                        </label>
                        <input 
                            type="password" 
                            id="password_confirmation" 
                            name="password_confirmation"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            placeholder="••••••••"
                        >
                    </div>
                </div>
            </div>

            <!-- Guest-Only Actions -->
            @if (Auth::user()->is_guest)
                <div class="border-b border-gray-200 pb-6 bg-green-50 p-4 rounded">
                    <h2 class="text-lg font-semibold text-gray-900 mb-4">🚀 Guest Account</h2>
                    <p class="text-sm text-gray-700 mb-4">
                        Your guest account will expire in {{ Auth::user()->token_expires_at->diffInHours(now()) }} hours.
                    </p>
                    <a 
                        href="{{ route('convert-to-user') }}"
                        class="inline-block bg-green-600 text-white py-2 px-6 rounded-lg font-medium hover:bg-green-700 transition duration-200"
                    >
                        ⭐ Upgrade to Premium Account
                    </a>
                </div>
            @endif

            <!-- Account Info -->
            <div class="bg-gray-50 p-4 rounded text-sm text-gray-600">
                <p><strong>Account Created:</strong> {{ Auth::user()->created_at->format('M d, Y H:i A') }}</p>
                @if (Auth::user()->is_guest && Auth::user()->token_expires_at)
                    <p><strong>Token Expires:</strong> {{ Auth::user()->token_expires_at->format('M d, Y H:i A') }}</p>
                @endif
            </div>

            <!-- Submit Buttons -->
            <div class="flex gap-4">
                <button 
                    type="submit"
                    class="bg-indigo-600 text-white py-2 px-8 rounded-lg font-medium hover:bg-indigo-700 transition duration-200"
                >
                    💾 Save Changes
                </button>
                <a 
                    href="{{ route('dashboard') }}"
                    class="bg-gray-300 text-gray-800 py-2 px-8 rounded-lg font-medium hover:bg-gray-400 transition duration-200"
                >
                    Cancel
                </a>
            </div>
        </form>
    </div>

    <!-- Danger Zone -->
    <div class="mt-8 bg-red-50 border border-red-200 rounded-lg p-8">
        <h2 class="text-lg font-bold text-red-900 mb-4">⚠️ Danger Zone</h2>
        
        <div class="space-y-4">
            <div>
                <h3 class="font-semibold text-red-900 mb-2">Delete Account</h3>
                <p class="text-sm text-red-700 mb-4">
                    Once you delete your account, there is no going back. Please be certain.
                </p>
                <button 
                    type="button"
                    onclick="if(confirm('Are you sure? This action cannot be undone.')) { document.getElementById('deleteForm').submit(); }"
                    class="bg-red-600 text-white py-2 px-6 rounded-lg font-medium hover:bg-red-700 transition duration-200"
                >
                    🗑️ Delete Account
                </button>
            </div>
        </div>
    </div>

    <!-- Hidden Delete Form -->
    <form id="deleteForm" method="POST" action="{{ route('profile.delete') }}" style="display: none;">
        @csrf
        @method('DELETE')
    </form>
</div>
@endsection
