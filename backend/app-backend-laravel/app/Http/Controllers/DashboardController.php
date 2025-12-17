<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;

class DashboardController extends Controller
{
    /**
     * Show dashboard
     */
    public function index(Request $request)
    {
        try {
            $user = Auth::user();

            Log::info('DashboardController::index start', [
                'user_id' => $user?->id,
                'role' => $user?->role,
                'is_guest' => $user?->is_guest,
                'api_token_present' => $user?->api_token ? true : false,
                'token_expires_at' => $user?->token_expires_at,
                'token_remaining_seconds' => $user?->getTokenRemainingSeconds(),
                'session_api_token' => $request->session()->get('api_token'),
            ]);
            
            // Redirect admin to admin dashboard
            if ($user->role > 0) {
                return redirect()->route('admin.dashboard');
            }
            
            $isGuest = $user->is_guest;
            $tokenStatus = null;
            
            if ($isGuest) {
                $tokenStatus = [
                    'is_valid' => $user->isTokenValid(),
                    'is_expired' => $user->isTokenExpired(),
                    'expires_at' => $user->token_expires_at,
                    'expires_in_seconds' => $user->getTokenRemainingSeconds(),
                ];
            }
            
            // Count products and comments for this user
            $productIds = $user->products()->pluck('id');
            $productCount = $productIds->count();
            $commentCount = \App\Models\Comment::whereIn('product_id', $productIds)->count();

            Log::info('DashboardController::index data', [
                'user_id' => $user->id,
                'product_ids_count' => $productCount,
                'comment_count' => $commentCount,
            ]);
            
            return view('guest.dashboard', [
                'user' => $user,
                'isGuest' => $isGuest,
                'tokenStatus' => $tokenStatus,
                'products' => $user->products()->latest()->paginate(10),
                'productCount' => $productCount,
                'commentCount' => $commentCount,
            ]);
        } catch (\Throwable $e) {
            Log::error('DashboardController::index error', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            return back()->withErrors([
                'error' => 'Dashboard error: ' . $e->getMessage(),
            ]);
        }
    }

    /**
     * Show profile
     */
    public function showProfile(Request $request)
    {
        $user = Auth::user();
        
        return view('guest.profile', [
            'user' => $user,
            'isGuest' => $user->is_guest,
        ]);
    }

    /**
     * Update profile
     */
    public function updateProfile(Request $request)
    {
        $user = Auth::user();
        
        $validated = $request->validate([
            'name' => 'nullable|string|max:255',
            'email' => 'nullable|email|unique:users,email,' . $user->id,
            'current_password' => 'nullable|string',
            'password' => 'nullable|string|min:8|confirmed',
        ]);

        try {
            // If changing password, validate current password
            if ($request->has('password') && $request->password) {
                if (!$request->has('current_password') || !$request->current_password) {
                    return back()->withErrors([
                        'current_password' => 'Current password is required to change password',
                    ]);
                }

                if (!\Illuminate\Support\Facades\Hash::check($request->current_password, $user->password)) {
                    return back()->withErrors([
                        'current_password' => 'Current password is incorrect',
                    ]);
                }

                $user->password = bcrypt($request->password);
            }

            if ($request->has('name') && $request->name) {
                $user->name = $request->name;
            }

            if ($request->has('email') && $request->email) {
                $user->email = $request->email;
            }

            $user->save();

            return back()->with('message', 'Profile updated successfully');
        } catch (\Exception $e) {
            return back()->withErrors([
                'error' => 'Failed to update profile: ' . $e->getMessage(),
            ]);
        }
    }

    /**
     * Logout user
     */
    public function logout(Request $request)
    {
        $user = Auth::user();
        
        // Revoke API token
        $user->update([
            'api_token' => null,
            'api_token_name' => null,
        ]);
        
        Auth::logout();
        $request->session()->invalidate();
        $request->session()->regenerateToken();
        
        return redirect('/login')->with('success', 'Logged out successfully');
    }

    /**
     * Show guest conversion form
     */
    public function showConvertForm()
    {
        $user = Auth::user();
        
        if (!$user->is_guest) {
            return redirect('/profile')->with('error', 'Only guest users can convert');
        }

        return view('guest.convert', ['user' => $user]);
    }

    /**
     * Convert guest account to regular user
     */
    public function convertToUser(Request $request)
    {
        $user = Auth::user();
        
        if (!$user->is_guest) {
            return back()->withErrors(['error' => 'Only guest users can convert']);
        }

        $validated = $request->validate([
            'email' => 'required|email|unique:users,email,' . $user->id,
            'password' => 'required|string|min:8|confirmed',
        ]);

        try {
            $user->update([
                'email' => $validated['email'],
                'password' => bcrypt($validated['password']),
                'is_guest' => false,
                'token_expires_at' => null, // Remove token expiration for regular users
            ]);

            return redirect('/dashboard')->with('success', 'Account upgraded to premium. Token no longer expires!');
        } catch (\Exception $e) {
            return back()->withErrors([
                'error' => 'Failed to upgrade account: ' . $e->getMessage(),
            ]);
        }
    }

    /**
     * Delete user account
     */
    public function deleteProfile(Request $request)
    {
        $user = Auth::user();

        try {
            $user->delete();
            Auth::logout();
            $request->session()->invalidate();
            $request->session()->regenerateToken();

            return redirect('/login')->with('success', 'Account deleted successfully');
        } catch (\Exception $e) {
            return back()->withErrors([
                'error' => 'Failed to delete account: ' . $e->getMessage(),
            ]);
        }
    }

    /**
     * Refresh guest token (for web interface)
     */
    public function refreshGuestToken(Request $request)
    {
        $user = Auth::user();

        if (!$user->is_guest) {
            return back()->withErrors(['error' => 'Only guest users can refresh tokens']);
        }

        try {
            // Generate new token with 1-day expiration
            $user->generateApiToken('guest-web-refresh', true);

            // Update session
            session([
                'api_token' => $user->api_token,
                'token_expires_at' => $user->token_expires_at,
            ]);

            return back()->with('success', 'Token refreshed! Valid for 24 more hours.');
        } catch (\Exception $e) {
            return back()->withErrors([
                'error' => 'Failed to refresh token: ' . $e->getMessage(),
            ]);
        }
    }
}
