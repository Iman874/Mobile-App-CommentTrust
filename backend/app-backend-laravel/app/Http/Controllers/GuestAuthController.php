<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use App\Models\User;
use Illuminate\Support\Str;
use Carbon\Carbon;
use Illuminate\Support\Facades\Log;

class GuestAuthController extends Controller
{
    /**
     * Login as guest - create or retrieve existing guest account
     * POST /api/guest/login
     * 
     * Request body is optional. Can include:
     * {
     *   "device_id": "unique device identifier (optional)",
     *   "device_name": "device name (optional)"
     * }
     */
    public function loginAsGuest(Request $request): JsonResponse
    {
        try {
            Log::info('Guest login request received', [
                'device_id' => $request->input('device_id'),
                'ip' => $request->ip(),
                'user_agent' => $request->userAgent(),
            ]);

            // Generate unique guest username format:
            // guest-YYYY-MM-DD-HH-am/pm-increment
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
            
            // Check if guest already exists (by device or session)
            $deviceId = $request->input('device_id');
            if ($deviceId) {
                $existingGuest = User::where('is_guest', true)
                    ->where('email', 'like', "%{$deviceId}%")
                    ->where('token_expires_at', '>', now())
                    ->first();
                
                if ($existingGuest && !$existingGuest->isTokenExpired()) {
                    Log::info('Reusing existing guest session', [
                        'guest_id' => $existingGuest->id,
                        'expires_at' => $existingGuest->token_expires_at,
                    ]);
                    // Return existing valid guest token
                    return response()->json([
                        'ok' => true,
                        'message' => 'Logged in as guest (existing session)',
                        'user' => [
                            'id' => $existingGuest->id,
                            'name' => $existingGuest->name,
                            'email' => $existingGuest->email,
                            'is_guest' => true,
                        ],
                        'api_token' => $this->getPlainToken($existingGuest),
                        'token_type' => 'Bearer',
                        'expires_at' => $existingGuest->token_expires_at,
                        'expires_in_seconds' => $existingGuest->getTokenRemainingSeconds(),
                    ]);
                }
            }
            
            // Create new guest account
            $guestUser = User::create([
                'name' => $guestUsername,
                'email' => $deviceId ? "{$guestUsername}-{$deviceId}@guest.local" : $guestEmail,
                'password' => bcrypt(Str::random(32)), // Random password, not used for guests
                'is_guest' => true,
                'is_active' => true,
            ]);
            
            // Generate API token with 1-day expiration
            $plainToken = $guestUser->generateApiToken('guest-auto', true);

            Log::info('Guest account created', [
                'guest_id' => $guestUser->id,
                'email' => $guestUser->email,
                'token_expires_at' => $guestUser->token_expires_at,
            ]);
            
            return response()->json([
                'ok' => true,
                'message' => 'Guest account created and logged in',
                'user' => [
                    'id' => $guestUser->id,
                    'name' => $guestUser->name,
                    'email' => $guestUser->email,
                    'is_guest' => true,
                ],
                'api_token' => $plainToken,
                'token_type' => 'Bearer',
                'expires_at' => $guestUser->token_expires_at,
                'expires_in_seconds' => $guestUser->getTokenRemainingSeconds(),
            ], 201);
        } catch (\Exception $e) {
            Log::error('Guest login failed', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);
            return response()->json([
                'ok' => false,
                'message' => 'Failed to create guest account',
                'error' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Refresh guest token if expired
     * POST /api/guest/refresh-token
     * Requires: api_token middleware
     */
    public function refreshGuestToken(Request $request): JsonResponse
    {
        $user = $request->user();
        
        if (!$user || !$user->is_guest) {
            return response()->json([
                'ok' => false,
                'message' => 'Only guest users can refresh token',
            ], 401);
        }
        
        // Generate new token with 1-day expiration
        $plainToken = $user->generateApiToken('guest-refreshed', true);
        
        return response()->json([
            'ok' => true,
            'message' => 'Token refreshed successfully',
            'api_token' => $plainToken,
            'token_type' => 'Bearer',
            'expires_at' => $user->token_expires_at,
            'expires_in_seconds' => $user->getTokenRemainingSeconds(),
        ]);
    }

    /**
     * Check guest token validity
     * GET /api/guest/token-status
     * Requires: api_token middleware
     */
    public function checkTokenStatus(Request $request): JsonResponse
    {
        $user = $request->user();
        
        if (!$user) {
            return response()->json([
                'ok' => false,
                'message' => 'Unauthorized',
            ], 401);
        }
        
        return response()->json([
            'ok' => true,
            'is_valid' => $user->isTokenValid(),
            'is_expired' => $user->isTokenExpired(),
            'expires_at' => $user->token_expires_at,
            'expires_in_seconds' => $user->getTokenRemainingSeconds(),
            'is_guest' => $user->is_guest,
        ]);
    }

    /**
     * Convert guest account to regular user account
     * POST /api/guest/convert-to-user
     * Requires: api_token middleware
     */
    public function convertToRegularUser(Request $request): JsonResponse
    {
        $request->validate([
            'email' => 'required|email|unique:users,email',
            'password' => 'required|string|min:8|confirmed',
            'name' => 'nullable|string|max:255',
        ]);
        
        $user = $request->user();
        
        if (!$user || !$user->is_guest) {
            return response()->json([
                'ok' => false,
                'message' => 'Only guest users can be converted',
            ], 401);
        }
        
        try {
            // Update user to be a regular user
            $user->update([
                'name' => $request->name ?? $user->name,
                'email' => $request->email,
                'password' => bcrypt($request->password),
                'is_guest' => false,
                'token_expires_at' => null, // Remove expiration
            ]);
            
            // Generate new token without expiration
            $plainToken = $user->generateApiToken('regular-user', false);
            
            return response()->json([
                'ok' => true,
                'message' => 'Account converted to regular user',
                'user' => [
                    'id' => $user->id,
                    'name' => $user->name,
                    'email' => $user->email,
                    'is_guest' => false,
                ],
                'api_token' => $plainToken,
                'token_type' => 'Bearer',
                'expires_at' => $user->token_expires_at,
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to convert account',
                'error' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Logout guest user
     * POST /api/guest/logout
     * Requires: api_token middleware
     */
    public function logoutGuest(Request $request): JsonResponse
    {
        $user = $request->user();
        
        if (!$user) {
            return response()->json([
                'ok' => false,
                'message' => 'Unauthorized',
            ], 401);
        }
        
        // Revoke token
        $user->update([
            'api_token' => null,
            'api_token_name' => null,
        ]);
        
        return response()->json([
            'ok' => true,
            'message' => 'Logged out successfully',
        ]);
    }

    /**
     * List all active guest accounts
     * GET /api/guest/list
     * Public endpoint - no authentication needed
     */
    public function listGuests(): JsonResponse
    {
        try {
            $guests = User::where('is_guest', true)
                ->where('is_active', true)
                ->select(['id', 'name', 'email', 'token_expires_at', 'created_at'])
                ->orderByDesc('created_at')
                ->get()
                ->map(function ($guest) {
                    return [
                        'id' => $guest->id,
                        'name' => $guest->name,
                        'email' => $guest->email,
                        'token_expires_at' => $guest->token_expires_at,
                        'is_valid' => !$guest->isTokenExpired(),
                        'created_at' => $guest->created_at->format('Y-m-d H:i:s'),
                    ];
                });

            return response()->json([
                'ok' => true,
                'message' => 'Guest list retrieved',
                'guests' => $guests,
                'total' => count($guests),
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to retrieve guest list',
                'error' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Login as an existing guest account
     * POST /api/guest/login-as-existing
     * Body: { "guest_id": 123 }
     * Public endpoint - no authentication needed
     */
    public function loginAsExistingGuest(Request $request): JsonResponse
    {
        try {
            $request->validate([
                'guest_id' => 'required|integer|exists:users,id',
            ]);

            Log::info('Guest login-as-existing request received', [
                'guest_id' => $request->input('guest_id'),
                'ip' => $request->ip(),
                'user_agent' => $request->userAgent(),
            ]);

            $guestId = $request->input('guest_id');
            
            // Fetch the guest user
            $guestUser = User::where('id', $guestId)
                ->where('is_guest', true)
                ->where('is_active', true)
                ->first();

            if (!$guestUser) {
                Log::warning('Guest login-as-existing failed: guest not found or inactive', [
                    'guest_id' => $guestId,
                ]);
                return response()->json([
                    'ok' => false,
                    'message' => 'Guest account not found or inactive',
                ], 404);
            }

            // Check if token is expired
            if ($guestUser->isTokenExpired()) {
                // Refresh the token with 1-day expiration
                $plainToken = $guestUser->generateApiToken('guest-refreshed', true);
                Log::info('Guest token refreshed during login', [
                    'guest_id' => $guestUser->id,
                    'expires_at' => $guestUser->token_expires_at,
                ]);
            } else {
                // Token still valid, retrieve existing
                $plainToken = $this->getPlainToken($guestUser);
                Log::info('Guest token reused during login', [
                    'guest_id' => $guestUser->id,
                    'expires_at' => $guestUser->token_expires_at,
                ]);
            }

            return response()->json([
                'ok' => true,
                'message' => 'Logged in as guest',
                'user' => [
                    'id' => $guestUser->id,
                    'name' => $guestUser->name,
                    'email' => $guestUser->email,
                    'is_guest' => true,
                ],
                'api_token' => $plainToken,
                'token_type' => 'Bearer',
                'expires_at' => $guestUser->token_expires_at,
                'expires_in_seconds' => $guestUser->getTokenRemainingSeconds(),
            ]);
        } catch (\Illuminate\Validation\ValidationException $e) {
            Log::warning('Guest login-as-existing validation failed', [
                'errors' => $e->errors(),
            ]);
            return response()->json([
                'ok' => false,
                'message' => 'Validation failed',
                'errors' => $e->errors(),
            ], 422);
        } catch (\Exception $e) {
            Log::error('Guest login-as-existing failed', [
                'guest_id' => $request->input('guest_id'),
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);
            return response()->json([
                'ok' => false,
                'message' => 'Failed to login as guest',
                'error' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Helper: Get plain token for user
     * This assumes we have just hashed the token and need to retrieve it
     * In production, you should return the plaintext before hashing
     */
    private function getPlainToken(User $user): string
    {
        // Since we can't retrieve the plain token from hash, 
        // this is a workaround - in production, store it temporarily
        // For now, generate a new one
        return $user->generateApiToken('guest-retrieve', true);
    }
}
