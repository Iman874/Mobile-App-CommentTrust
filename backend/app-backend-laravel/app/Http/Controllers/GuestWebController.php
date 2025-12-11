<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\User;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Carbon\Carbon;

class GuestWebController extends Controller
{
    /**
     * Show login form
     */
    public function showLoginForm()
    {
        return view('guest.login');
    }

    /**
     * Show register form
     */
    public function showRegisterForm()
    {
        return view('guest.register');
    }

    /**
     * Handle login submission (regular user)
     */
    public function login(Request $request)
    {
        $credentials = $request->validate([
            'email' => 'required|email',
            'password' => 'required|string',
        ]);

        // Attempt login
        if (Auth::attempt($credentials, $request->boolean('remember'))) {
            $request->session()->regenerate();
            
            // Cache the login type for later
            session(['login_type' => 'regular', 'logged_in_at' => now()]);
            
            return redirect('/dashboard');
        }

        return back()->withErrors([
            'email' => 'The provided credentials do not match our records.',
        ])->onlyInput('email');
    }

    /**
     * Handle guest login
     * This creates a guest account automatically
     */
    public function guestLogin(Request $request)
    {
        try {
            // Generate unique guest username
            $now = Carbon::now();
            $date = $now->format('Y-m-d');
            $time = $now->format('h');
            $period = $now->format('a'); // am/pm
            
            // Get the highest increment for today
            $baseUsername = "guest-{$date}-{$time}-{$period}";
            $existingCount = User::where('name', 'like', "{$baseUsername}-%")
                ->count();
            
            $increment = $existingCount + 1;
            $guestUsername = "{$baseUsername}-{$increment}";
            $guestEmail = "{$guestUsername}@guest.local";
            
            // Create guest user
            $guestUser = User::create([
                'name' => $guestUsername,
                'email' => $guestEmail,
                'password' => bcrypt(\Illuminate\Support\Str::random(32)),
                'is_guest' => true,
                'is_active' => true,
            ]);
            
            // Generate API token with 1-day expiration
            $guestUser->generateApiToken('guest-web-login', true);
            
            // Log in the user
            Auth::login($guestUser);
            $request->session()->regenerate();
            
            // Cache login info
            session([
                'login_type' => 'guest',
                'logged_in_at' => now(),
                'api_token' => $guestUser->api_token,
                'token_expires_at' => $guestUser->token_expires_at,
            ]);
            
            return redirect('/dashboard')->with('message', 'Logged in as guest user');
        } catch (\Exception $e) {
            return back()->withErrors([
                'error' => 'Failed to create guest account: ' . $e->getMessage(),
            ]);
        }
    }

    /**
     * Handle register submission (create regular user)
     */
    public function register(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:users,email',
            'password' => 'required|string|min:8|confirmed',
        ]);

        try {
            // Create user
            $user = User::create([
                'name' => $validated['name'],
                'email' => $validated['email'],
                'password' => Hash::make($validated['password']),
                'is_guest' => false,
                'is_active' => true,
            ]);
            
            // Log in the user
            Auth::login($user);
            $request->session()->regenerate();
            
            // Cache login info
            session([
                'login_type' => 'regular',
                'logged_in_at' => now(),
            ]);
            
            return redirect('/dashboard')->with('message', 'Account created and logged in');
        } catch (\Exception $e) {
            return back()->withErrors([
                'error' => 'Failed to create account: ' . $e->getMessage(),
            ])->withInput();
        }
    }
}
