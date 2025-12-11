@extends('layouts.app')

@section('title', 'Login - CommentTrust')

@section('content')
<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
    <div class="w-full max-w-md bg-white rounded-lg shadow-xl p-8">
        <div class="text-center mb-8">
            <h1 class="text-3xl font-bold text-indigo-600 mb-2">CommentTrust</h1>
            <p class="text-gray-600">Analyze product reviews with AI</p>
        </div>

        @if ($errors->any())
            <div class="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                @foreach ($errors->all() as $error)
                    <p>{{ $error }}</p>
                @endforeach
            </div>
        @endif

        <!-- Regular Login Form -->
        <form method="POST" action="{{ route('login.post') }}" class="space-y-4">
            @csrf
            
            <div>
                <label for="email" class="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                <input 
                    type="email" 
                    id="email" 
                    name="email" 
                    required 
                    value="{{ old('email') }}"
                    class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="you@example.com"
                >
            </div>

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
            </div>

            <div class="flex items-center">
                <input 
                    type="checkbox" 
                    id="remember" 
                    name="remember" 
                    {{ old('remember') ? 'checked' : '' }}
                    class="h-4 w-4 text-indigo-600 rounded"
                >
                <label for="remember" class="ml-2 text-sm text-gray-700">Remember me</label>
            </div>

            <button 
                type="submit"
                class="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-indigo-700 transition duration-200"
            >
                Login
            </button>
        </form>

        <div class="my-6 flex items-center">
            <div class="flex-1 border-t border-gray-300"></div>
            <div class="px-3 text-gray-500 text-sm">OR</div>
            <div class="flex-1 border-t border-gray-300"></div>
        </div>

        <!-- Guest Login Form -->
        <form method="POST" action="{{ route('guest.login') }}" class="mb-4">
            @csrf
            <button 
                type="submit"
                class="w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white py-2 px-4 rounded-lg font-medium hover:from-green-600 hover:to-emerald-600 transition duration-200"
            >
                🚀 Login as Guest
            </button>
            <p class="text-xs text-gray-500 text-center mt-2">
                No account needed. Valid for 24 hours.
            </p>
        </form>

        <!-- Register Link -->
        <div class="text-center border-t border-gray-200 pt-4">
            <p class="text-gray-600 text-sm">Don't have an account?</p>
            <a href="{{ route('register') }}" class="text-indigo-600 font-medium hover:underline">
                Create account
            </a>
        </div>
    </div>
</div>
@endsection
