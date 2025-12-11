@extends('layouts.app')

@section('title', 'Upgrade Account - CommentTrust')

@section('content')
<div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="bg-white rounded-lg shadow p-8">
        <div class="text-center mb-8">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">⭐ Upgrade to Premium</h1>
            <p class="text-gray-600">Convert your guest account to a permanent account</p>
        </div>

        <!-- Benefits Section -->
        <div class="grid md:grid-cols-2 gap-6 mb-8">
            <div class="border border-gray-200 rounded-lg p-6">
                <h3 class="font-semibold text-gray-900 mb-3">🚀 Guest Account (Current)</h3>
                <ul class="space-y-2 text-sm text-gray-700">
                    <li class="flex items-center gap-2">
                        <span class="text-yellow-500">⏱️</span>
                        24-hour expiration
                    </li>
                    <li class="flex items-center gap-2">
                        <span class="text-yellow-500">🔄</span>
                        Token refresh required
                    </li>
                    <li class="flex items-center gap-2">
                        <span class="text-yellow-500">🔒</span>
                        No password set
                    </li>
                    <li class="flex items-center gap-2">
                        <span class="text-yellow-500">⚠️</span>
                        Limited features
                    </li>
                </ul>
            </div>

            <div class="border border-green-200 rounded-lg p-6 bg-green-50">
                <h3 class="font-semibold text-gray-900 mb-3">⭐ Premium Account</h3>
                <ul class="space-y-2 text-sm text-gray-700">
                    <li class="flex items-center gap-2">
                        <span class="text-green-500">✓</span>
                        Unlimited access
                    </li>
                    <li class="flex items-center gap-2">
                        <span class="text-green-500">✓</span>
                        No token refresh
                    </li>
                    <li class="flex items-center gap-2">
                        <span class="text-green-500">✓</span>
                        Secure password login
                    </li>
                    <li class="flex items-center gap-2">
                        <span class="text-green-500">✓</span>
                        All features available
                    </li>
                </ul>
            </div>
        </div>

        <!-- Warning -->
        <div class="mb-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p class="text-sm text-blue-700">
                <strong>ℹ️ Note:</strong> Your current guest username and all data will be preserved. You just need to set up a password.
            </p>
        </div>

        @if ($errors->any())
            <div class="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                <p class="font-medium mb-2">Upgrade failed:</p>
                @foreach ($errors->all() as $error)
                    <p class="text-sm">• {{ $error }}</p>
                @endforeach
            </div>
        @endif

        <!-- Conversion Form -->
        <form method="POST" action="{{ route('convert-to-user.post') }}" class="space-y-6">
            @csrf

            <div class="border-b border-gray-200 pb-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">Account Setup</h2>
                
                <div class="space-y-4">
                    <div>
                        <label for="username" class="block text-sm font-medium text-gray-700 mb-2">Current Username</label>
                        <input 
                            type="text" 
                            id="username" 
                            value="{{ Auth::user()->name }}"
                            disabled
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-600"
                        >
                        <p class="text-xs text-gray-500 mt-1">This will not change</p>
                    </div>

                    <div>
                        <label for="email" class="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                        <input 
                            type="email" 
                            id="email" 
                            name="email" 
                            required
                            value="{{ old('email', Auth::user()->email) }}"
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            placeholder="your@email.com"
                        >
                        @error('email')
                            <p class="text-red-500 text-xs mt-1">{{ $message }}</p>
                        @enderror
                    </div>
                </div>
            </div>

            <div class="border-b border-gray-200 pb-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">Set Password</h2>
                <p class="text-sm text-gray-600 mb-4">
                    Create a secure password to protect your account.
                </p>
                
                <div class="space-y-4">
                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-700 mb-2">Password</label>
                        <input 
                            type="password" 
                            id="password" 
                            name="password" 
                            required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            placeholder="••••••••"
                        >
                        @error('password')
                            <p class="text-red-500 text-xs mt-1">{{ $message }}</p>
                        @enderror
                        <p class="text-xs text-gray-500 mt-1">At least 8 characters. Use uppercase, lowercase, numbers, and symbols for better security.</p>
                    </div>

                    <div>
                        <label for="password_confirmation" class="block text-sm font-medium text-gray-700 mb-2">Confirm Password</label>
                        <input 
                            type="password" 
                            id="password_confirmation" 
                            name="password_confirmation" 
                            required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            placeholder="••••••••"
                        >
                    </div>
                </div>
            </div>

            <!-- Terms -->
            <div class="bg-gray-50 p-4 rounded">
                <div class="flex items-start gap-3">
                    <input 
                        type="checkbox" 
                        id="agree" 
                        name="agree" 
                        required
                        class="h-4 w-4 mt-1"
                    >
                    <label for="agree" class="text-sm text-gray-700">
                        I understand this action is permanent and my guest token will no longer expire. 
                        I agree to the Terms of Service.
                    </label>
                </div>
            </div>

            <!-- Submit Buttons -->
            <div class="flex gap-4">
                <button 
                    type="submit"
                    class="bg-green-600 text-white py-2 px-8 rounded-lg font-medium hover:bg-green-700 transition duration-200 flex-1"
                >
                    ✓ Upgrade Account
                </button>
                <a 
                    href="{{ route('dashboard') }}"
                    class="bg-gray-300 text-gray-800 py-2 px-8 rounded-lg font-medium hover:bg-gray-400 transition duration-200 flex-1 text-center"
                >
                    Cancel
                </a>
            </div>
        </form>
    </div>

    <!-- Token Status Info -->
    <div class="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h3 class="font-bold text-yellow-900 mb-3">⏱️ Current Token Status</h3>
        <div class="grid md:grid-cols-2 gap-4 text-sm">
            <div>
                <p class="text-gray-600">Expires At:</p>
                <p class="font-mono text-gray-900">{{ Auth::user()->token_expires_at->format('M d, Y H:i A') }}</p>
            </div>
            <div>
                <p class="text-gray-600">Time Remaining:</p>
                <p class="font-mono text-gray-900">
                    {{ Auth::user()->token_expires_at->diffInHours(now()) }} hours
                </p>
            </div>
        </div>
    </div>
</div>
@endsection
