<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'Admin Dashboard - CommentTrust')</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
<div class="flex h-screen bg-gray-100">
    <!-- Sidebar Navigation -->
    <div class="w-64 bg-indigo-900 text-white shadow-lg">
        <div class="p-6 border-b border-indigo-800">
            <h1 class="text-2xl font-bold">CommentTrust</h1>
            <p class="text-sm text-indigo-300 mt-1">Admin Panel</p>
        </div>

        <nav class="mt-6">
            <a href="{{ route('admin.dashboard') }}" class="flex items-center px-6 py-3 text-indigo-100 hover:bg-indigo-800 transition {{ request()->routeIs('admin.dashboard') ? 'bg-indigo-700 text-white border-l-4 border-blue-400' : '' }}">
                <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-3m0 0l7-4 7 4M5 10v10a1 1 0 001 1h12a1 1 0 001-1V10M9 21h6"></path>
                </svg>
                Dashboard
            </a>

            <a href="{{ route('admin.users') }}" class="flex items-center px-6 py-3 text-indigo-100 hover:bg-indigo-800 transition {{ request()->routeIs('admin.users*') ? 'bg-indigo-700 text-white border-l-4 border-blue-400' : '' }}">
                <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-2a6 6 0 0112 0v2zm0 0h6v-2a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path>
                </svg>
                User Management
            </a>

            <a href="{{ route('admin.jobs') }}" class="flex items-center px-6 py-3 text-indigo-100 hover:bg-indigo-800 transition {{ request()->routeIs('admin.jobs*') ? 'bg-indigo-700 text-white border-l-4 border-blue-400' : '' }}">
                <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
                Job Management
            </a>

            <a href="{{ route('admin.api-tester') }}" class="flex items-center px-6 py-3 text-indigo-100 hover:bg-indigo-800 transition {{ request()->routeIs('admin.api-tester*') ? 'bg-indigo-700 text-white border-l-4 border-blue-400' : '' }}">
                <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20m0 0l-.75 3M9 20a6 6 0 1112 0m0 0l.75 3M21 20l.75-3M3 13h18"></path>
                </svg>
                API Tester
            </a>

            <div class="border-t border-indigo-800 mt-6 pt-6">
                <form method="POST" action="{{ route('logout') }}">
                    @csrf
                    <button type="submit" class="flex items-center px-6 py-3 text-red-300 hover:text-red-200 hover:bg-indigo-800 transition w-full">
                        <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                        </svg>
                        Logout
                    </button>
                </form>
            </div>
        </nav>
    </div>

    <!-- Main Content -->
    <div class="flex-1 overflow-auto">
        <!-- Top Bar -->
        <div class="bg-white shadow-sm border-b border-gray-200">
            <div class="px-6 py-4 flex justify-between items-center">
                <div>
                    <h2 class="text-2xl font-bold text-gray-900">@yield('page-title', 'Dashboard')</h2>
                    <p class="text-sm text-gray-600 mt-1">@yield('page-subtitle', '')</p>
                </div>
                <div class="flex items-center gap-4">
                    <div class="text-right">
                        <p class="text-sm font-medium text-gray-900">{{ Auth::user()->name }}</p>
                        <p class="text-xs text-gray-600">Administrator</p>
                    </div>
                    <img src="https://ui-avatars.com/api/?name={{ Auth::user()->name }}" alt="Avatar" class="w-10 h-10 rounded-full">
                </div>
            </div>
        </div>

        <!-- Page Content -->
        <div class="p-6">
            @if (session('success'))
                <div class="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
                    {{ session('success') }}
                </div>
            @endif

            @if (session('error'))
                <div class="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                    {{ session('error') }}
                </div>
            @endif

            @if ($errors->any())
                <div class="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                    @foreach ($errors->all() as $error)
                        <p>{{ $error }}</p>
                    @endforeach
                </div>
            @endif

            @yield('admin-content')
        </div>
    </div>
</div>
</body>
</html>
