@extends('layouts.app')

@section('content')
<div class="min-h-screen flex">
    <!-- Left side - Illustration -->
    <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-indigo-600 to-blue-600 items-center justify-center p-8">
        <div class="text-white text-center">
            <svg class="w-24 h-24 mx-auto mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
            <h1 class="text-4xl font-bold mb-4">Admin Panel</h1>
            <p class="text-indigo-100 text-lg">Manage users, monitor jobs, and test API endpoints</p>
        </div>
    </div>

    <!-- Right side - Login Form -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-8 bg-gray-50">
        <div class="w-full max-w-md">
            <div class="bg-white rounded-lg shadow p-8">
                <h2 class="text-3xl font-bold text-gray-900 mb-2">Admin Login</h2>
                <p class="text-gray-600 mb-8">Sign in to your administrator account</p>

                <!-- Display errors -->
                @if ($errors->any())
                    <div class="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                        <div class="flex">
                            <div class="flex-shrink-0">
                                <svg class="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
                                </svg>
                            </div>
                            <div class="ml-3">
                                <h3 class="text-sm font-medium text-red-800">Error</h3>
                                <div class="mt-2 text-sm text-red-700">
                                    <ul class="list-disc list-inside">
                                        @foreach ($errors->all() as $error)
                                            <li>{{ $error }}</li>
                                        @endforeach
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                @endif

                <!-- Display status message -->
                @if (session('status'))
                    <div class="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
                        <div class="flex">
                            <div class="flex-shrink-0">
                                <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                </svg>
                            </div>
                            <div class="ml-3">
                                <p class="text-sm font-medium text-green-800">{{ session('status') }}</p>
                            </div>
                        </div>
                    </div>
                @endif

                <form method="POST" action="{{ route('admin.login') }}" class="space-y-6">
                    @csrf

                    <!-- Username -->
                    <div>
                        <label for="username" class="block text-sm font-medium text-gray-700 mb-2">Username</label>
                        <input type="text" name="username" id="username" value="{{ old('username') }}" required autofocus
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 @error('username') border-red-500 @enderror">
                        @error('username')
                            <p class="mt-1 text-sm text-red-600">{{ $message }}</p>
                        @enderror
                    </div>

                    <!-- Password -->
                    <div>
                        <label for="password" class="block text-sm font-medium text-gray-700 mb-2">Password</label>
                        <input type="password" name="password" id="password" required
                            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 @error('password') border-red-500 @enderror">
                        @error('password')
                            <p class="mt-1 text-sm text-red-600">{{ $message }}</p>
                        @enderror
                    </div>

                    <!-- Remember Me -->
                    <div class="flex items-center">
                        <input type="checkbox" name="remember" id="remember" class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded">
                        <label for="remember" class="ml-2 block text-sm text-gray-700">Remember me</label>
                    </div>

                    <!-- Submit Button -->
                    <button type="submit" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-indigo-700 transition">
                        Sign In
                    </button>
                </form>

                <!-- Alternative - Guest Login -->
                <div class="mt-6 pt-6 border-t border-gray-200">
                    <p class="text-center text-gray-600 mb-4">Or login with your guest account</p>
                    <a href="{{ route('login') }}" class="block w-full text-center px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition font-medium">
                        Guest Login
                    </a>
                </div>
            </div>

            <!-- Footer -->
            <p class="mt-8 text-center text-gray-500 text-sm">
                Protected Admin Area - Unauthorized access is prohibited
            </p>
        </div>
    </div>
</div>
@endsection
