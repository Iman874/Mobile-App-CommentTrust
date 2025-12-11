<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Str;
use App\Models\User;
use App\Models\Product;

class UserManagementController extends Controller
{
    /**
     * Show user management page
     * Only show non-admin users (role = 0)
     */
    public function index()
    {
        $users = User::where('role', 0)
            ->withCount('products')
            ->orderBy('created_at', 'desc')
            ->paginate(20);

        return view('admin.users.index', compact('users'));
    }

    /**
     * Show user detail page
     * Only allow viewing non-admin users
     */
    public function show($id)
    {
        $user = User::with('products')->findOrFail($id);
        
        // Prevent admin from viewing other admin accounts
        if ($user->role > 0) {
            abort(403, 'Cannot view admin user details');
        }

        $productsCount = $user->products()->count();
        $commentsCount = \DB::table('comments')
            ->whereIn('product_id', $user->products()->pluck('id'))
            ->count();
        $scrapedCount = $user->products()->whereNotNull('created_at')->count();
        $analyzedCount = $user->products()->where('is_analyzed', true)->count();

        $products = $user->products()
            ->withCount('comments')
            ->orderBy('created_at', 'desc')
            ->get();

        return view('admin.users.show', compact(
            'user',
            'productsCount',
            'commentsCount',
            'scrapedCount',
            'analyzedCount',
            'products'
        ));
    }

    /**
     * List users (API)
     * Only return non-admin users (role = 0)
     */
    public function list()
    {
        $users = User::where('role', 0)
            ->withCount('products')
            ->orderBy('created_at', 'desc')
            ->paginate(20);

        return response()->json([
            'ok' => true,
            'users' => $users
        ]);
    }

    /**
     * Update user (API)
     */
    public function update(Request $request, $id)
    {
        $user = User::findOrFail($id);

        $request->validate([
            'name' => 'sometimes|string|max:255',
            'email' => 'sometimes|email|max:255|unique:users,email,' . $id,
        ]);

        $user->update($request->only(['name', 'email']));

        return response()->json([
            'ok' => true,
            'message' => 'User updated successfully',
            'user' => $user
        ]);
    }

    /**
     * Delete user (API)
     * Prevent deleting admin users
     */
    public function destroy($id)
    {
        $user = User::findOrFail($id);
        
        // Prevent deleting admin users
        if ($user->role > 0) {
            return response()->json([
                'ok' => false,
                'message' => 'Cannot delete admin users'
            ], 403);
        }

        // Delete user's products and comments
        $user->products()->delete();

        // Delete user
        $user->delete();

        return response()->json([
            'ok' => true,
            'message' => 'User deleted successfully'
        ]);
    }

    /**
     * Refresh user's API token (API)
     */
    public function refreshToken($id)
    {
        $user = User::findOrFail($id);

        $user->api_token = Str::random(80);
        $user->token_expires_at = now()->addDays(7);
        $user->save();

        return response()->json([
            'ok' => true,
            'message' => 'Token refreshed successfully',
            'new_token' => $user->api_token,
            'expires_at' => $user->token_expires_at->toDateTimeString()
        ]);
    }

    /**
     * Extend user's token expiration (API)
     */
    public function extendToken($id)
    {
        $user = User::findOrFail($id);

        $user->token_expires_at = $user->token_expires_at->addDays(7);
        $user->save();

        return response()->json([
            'ok' => true,
            'message' => 'Token extended by 7 days',
            'expires_at' => $user->token_expires_at->toDateTimeString()
        ]);
    }

    /**
     * Reset user's sessions (API)
     */
    public function resetSessions($id)
    {
        $user = User::findOrFail($id);

        // Delete all sessions for this user
        \DB::table('sessions')->where('user_id', $id)->delete();

        return response()->json([
            'ok' => true,
            'message' => 'All sessions reset successfully'
        ]);
    }
}
