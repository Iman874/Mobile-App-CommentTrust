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

        <!-- Guest Login Section -->
        <div id="guestSection" class="space-y-4">
            <!-- Loading indicator -->
            <div id="guestLoading" class="text-center py-4">
                <div class="inline-block animate-spin">
                    <svg class="w-6 h-6 text-green-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                </div>
                <p class="text-gray-600 text-sm mt-2">Loading available guest accounts...</p>
            </div>

            <!-- Guest list container (hidden until loaded) -->
            <div id="guestListContainer" class="hidden space-y-3">
                <label class="block text-sm font-medium text-gray-700">Select or Create Guest Account</label>
                <div id="guestList" class="space-y-2 max-h-48 overflow-y-auto border border-gray-200 rounded-lg p-3 bg-gray-50">
                    <!-- Guest options will be injected here -->
                </div>
            </div>

            <!-- Submit button (hidden until loaded) -->
            <button 
                type="button"
                id="guestSubmitBtn"
                onclick="submitGuestLogin()"
                class="hidden w-full bg-gradient-to-r from-green-500 to-emerald-500 text-white py-2 px-4 rounded-lg font-medium hover:from-green-600 hover:to-emerald-600 transition duration-200"
            >
                🚀 Login as Guest
            </button>

            <p class="text-xs text-gray-500 text-center">
                No account needed. Guest accounts valid for 24 hours.
            </p>
        </div>

        <!-- Register Link -->
        <div class="text-center border-t border-gray-200 pt-4">
            <p class="text-gray-600 text-sm">Don't have an account?</p>
            <a href="{{ route('register') }}" class="text-indigo-600 font-medium hover:underline">
                Create account
            </a>
        </div>
    </div>
</div>

<script>
    let selectedGuestId = null;

    // Load guest list on page load
    document.addEventListener('DOMContentLoaded', function() {
        loadGuestList();
    });

    async function loadGuestList() {
        try {
            const response = await fetch('/api/guest/list');
            const data = await response.json();

            if (!data.ok) {
                throw new Error(data.message || 'Failed to load guest list');
            }

            const guests = data.guests || [];
            const guestList = document.getElementById('guestList');
            const guestListContainer = document.getElementById('guestListContainer');
            const guestSubmitBtn = document.getElementById('guestSubmitBtn');
            const guestLoading = document.getElementById('guestLoading');

            // Clear loading indicator
            guestLoading.classList.add('hidden');

            if (guests.length === 0) {
                // No existing guests, show create new button
                guestList.innerHTML = `
                    <div class="flex items-center p-3 bg-white border border-gray-200 rounded cursor-pointer hover:bg-green-50 transition" onclick="selectGuest(null)">
                        <input type="radio" name="guest" value="new" class="h-4 w-4 text-green-600" checked>
                        <label class="ml-3 flex-1 cursor-pointer">
                            <span class="font-medium text-green-600">Create New Guest Account</span>
                            <p class="text-xs text-gray-500">New session, valid for 24 hours</p>
                        </label>
                    </div>
                `;
                selectedGuestId = null;
            } else {
                // Show existing guests + create new option
                let html = '';

                // Add create new option first
                html += `
                    <div class="flex items-center p-3 bg-white border border-gray-200 rounded cursor-pointer hover:bg-green-50 transition" onclick="selectGuest(null)">
                        <input type="radio" name="guest" value="new" class="h-4 w-4 text-green-600">
                        <label class="ml-3 flex-1 cursor-pointer">
                            <span class="font-medium text-green-600">Create New Guest Account</span>
                            <p class="text-xs text-gray-500">New session, valid for 24 hours</p>
                        </label>
                    </div>
                `;

                // Add existing guests
                guests.forEach(guest => {
                    const isValid = guest.is_valid ? '✓ Valid' : '⚠ Expired';
                    const validClass = guest.is_valid ? 'text-green-600' : 'text-red-600';
                    const expiresAt = new Date(guest.token_expires_at).toLocaleString();

                    html += `
                        <div class="flex items-center p-3 bg-white border border-gray-200 rounded cursor-pointer hover:bg-blue-50 transition" onclick="selectGuest(${guest.id})">
                            <input type="radio" name="guest" value="guest-${guest.id}" class="h-4 w-4 text-blue-600">
                            <label class="ml-3 flex-1 cursor-pointer">
                                <span class="font-medium text-gray-800">${guest.name}</span>
                                <p class="text-xs text-gray-500">${guest.email}</p>
                                <p class="text-xs ${validClass}">${isValid} • Expires: ${expiresAt}</p>
                            </label>
                        </div>
                    `;
                });

                guestList.innerHTML = html;
                selectedGuestId = null; // Default to create new
            }

            guestListContainer.classList.remove('hidden');
            guestSubmitBtn.classList.remove('hidden');
        } catch (error) {
            console.error('Error loading guest list:', error);
            const guestList = document.getElementById('guestList');
            const guestLoading = document.getElementById('guestLoading');
            
            guestLoading.innerHTML = `
                <div class="text-center py-4">
                    <p class="text-red-600 text-sm mb-2">Failed to load guest accounts</p>
                    <button type="button" onclick="loadGuestList()" class="text-blue-600 text-sm hover:underline">
                        Retry
                    </button>
                </div>
            `;
        }
    }

    function selectGuest(guestId) {
        selectedGuestId = guestId;
        // Update radio button
        const radios = document.querySelectorAll('input[name="guest"]');
        radios.forEach(radio => {
            if (guestId === null) {
                radio.checked = radio.value === 'new';
            } else {
                radio.checked = radio.value === `guest-${guestId}`;
            }
        });
    }

    async function submitGuestLogin() {
        const btn = document.getElementById('guestSubmitBtn');
        btn.disabled = true;
        btn.textContent = '🔄 Logging in...';

        try {
            const payload = selectedGuestId === null ? {} : { guest_id: selectedGuestId };

            const response = await fetch('/guest-login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.content || ''
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!data.ok) {
                throw new Error(data.message || 'Failed to login as guest');
            }

            // Store token and redirect (web session already created server-side)
            if (data.api_token) {
                localStorage.setItem('api_token', data.api_token);
            }
            window.location.href = data.redirect || '/dashboard';
        } catch (error) {
            console.error('Error during guest login:', error);
            alert('Login failed: ' + error.message);
            btn.disabled = false;
            btn.textContent = '🚀 Login as Guest';
        }
    }
</script>
@endsection
