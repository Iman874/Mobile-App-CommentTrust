<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use App\Models\User;

class AdminAuthController extends Controller
{
    /**
     * Show admin login form
     */
    public function showLoginForm()
    {
        return view('admin.auth.login');
    }

    /**
     * Handle admin login
     */
    public function login(Request $request)
    {
        $request->validate([
            'username' => 'required|string',
            'password' => 'required|string',
        ]);

        $credentials = [
            'username' => $request->username,
            'password' => $request->password,
        ];

        // Attempt authentication
        if (Auth::attempt($credentials, $request->filled('remember'))) {
            $user = Auth::user();

            // Check if user has admin role
            if ($user->role == 0) {
                Auth::logout();
                return back()->withErrors([
                    'username' => 'You do not have admin access.',
                ])->withInput();
            }

            $request->session()->regenerate();

            return redirect()->intended(route('admin.dashboard'))
                ->with('success', 'Welcome back, ' . $user->name . '!');
        }

        return back()->withErrors([
            'username' => 'The provided credentials do not match our records.',
        ])->withInput();
    }

    /**
     * Handle admin logout
     */
    public function logout(Request $request)
    {
        Auth::logout();

        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return redirect()->route('admin.auth.login')
            ->with('status', 'You have been logged out successfully.');
    }
}
