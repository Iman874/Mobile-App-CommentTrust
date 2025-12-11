<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'CommentTrust')</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        [v-cloak] { display: none; }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Navigation -->
    @auth
        <nav class="bg-white shadow">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex items-center">
                        <a href="{{ route('dashboard') }}" class="flex items-center space-x-2">
                            <span class="text-2xl font-bold text-indigo-600">CommentTrust</span>
                        </a>
                    </div>
                    <div class="flex items-center space-x-4">
                        <div class="text-sm">
                            <p class="text-gray-900 font-medium">{{ Auth::user()->name }}</p>
                            @if (Auth::user()->is_guest)
                                <span class="inline-block mt-1 px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">
                                    👤 Guest User
                                </span>
                            @endif
                        </div>
                        <div class="relative group">
                            <button class="text-gray-700 hover:text-gray-900 font-medium py-2 px-3 rounded">
                                Menu
                            </button>
                            <div class="absolute right-0 w-48 bg-white rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10">
                                <a href="{{ route('dashboard') }}" class="block px-4 py-2 text-gray-700 hover:bg-gray-100">
                                    📊 Dashboard
                                </a>
                                <a href="{{ route('profile') }}" class="block px-4 py-2 text-gray-700 hover:bg-gray-100">
                                    👤 Profile
                                </a>
                                <form method="POST" action="{{ route('logout') }}" class="block">
                                    @csrf
                                    <button type="submit" class="w-full text-left px-4 py-2 text-gray-700 hover:bg-gray-100">
                                        🚪 Logout
                                    </button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    @endauth

    <!-- Flash Messages -->
    @if (session('success'))
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
            <div class="p-4 bg-green-100 border border-green-400 text-green-700 rounded">
                {{ session('success') }}
            </div>
        </div>
    @endif

    @if (session('error'))
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
            <div class="p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                {{ session('error') }}
            </div>
        </div>
    @endif

    <!-- Main Content -->
    <main>
        @yield('content')
    </main>

    <!-- Footer -->
    <footer class="bg-white border-t border-gray-200 mt-12 py-6">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-600 text-sm">
            <p>&copy; {{ date('Y') }} CommentTrust. All rights reserved.</p>
            <p class="mt-2">Powered by AI | Protecting trust in product reviews</p>
        </div>
    </footer>

    @yield('scripts')
</body>
</html>
