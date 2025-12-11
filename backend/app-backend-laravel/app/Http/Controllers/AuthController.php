<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use App\Models\User;
use Illuminate\Support\Str;
use Illuminate\Support\Facades\Hash;

class AuthController extends Controller
{
    /**
     * Register new user
     * POST /api/auth/register
     */
    public function register(Request $request): JsonResponse
    {
        $request->validate([
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:users,email',
            'password' => 'required|string|min:8|confirmed',
        ]);

        try {
            // Create user
            $user = User::create([
                'name' => $request->name,
                'email' => $request->email,
                'password' => Hash::make($request->password),
            ]);

            // Generate API token
            $token = $this->generateApiToken($user);

            return response()->json([
                'ok' => true,
                'message' => 'User registered successfully',
                'user' => [
                    'id' => $user->id,
                    'name' => $user->name,
                    'email' => $user->email,
                ],
                'api_token' => $token,
                'token_type' => 'Bearer',
            ], 201);
        } catch (\Exception $e) {
            return response()->json([
                'ok' => false,
                'message' => 'Registration failed',
                'error' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Login user
     * POST /api/auth/login
     */
    public function login(Request $request): JsonResponse
    {
        $request->validate([
            'email' => 'required|email',
            'password' => 'required|string',
        ]);

        // Find user by email
        $user = User::where('email', $request->email)->first();

        if (!$user || !Hash::check($request->password, $user->password)) {
            return response()->json([
                'ok' => false,
                'message' => 'Invalid email or password',
            ], 401);
        }

        // Generate or refresh API token
        $token = $this->generateApiToken($user);

        return response()->json([
            'ok' => true,
            'message' => 'Login successful',
            'user' => [
                'id' => $user->id,
                'name' => $user->name,
                'email' => $user->email,
            ],
            'api_token' => $token,
            'token_type' => 'Bearer',
        ]);
    }

    /**
     * Get current authenticated user
     * GET /api/auth/me
     * Requires: api_token middleware
     */
    public function me(Request $request): JsonResponse
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
            'user' => [
                'id' => $user->id,
                'name' => $user->name,
                'email' => $user->email,
                'created_at' => $user->created_at,
                'updated_at' => $user->updated_at,
            ]
        ]);
    }

    /**
     * Generate new API token
     * POST /api/auth/token/generate
     * Requires: api_token middleware
     */
    public function generateNewToken(Request $request): JsonResponse
    {
        $request->validate([
            'token_name' => 'nullable|string|max:255',
        ]);

        $user = $request->user();

        if (!$user) {
            return response()->json([
                'ok' => false,
                'message' => 'Unauthorized',
            ], 401);
        }

        try {
            // For guest users, regenerate with expiration
            // For regular users, no expiration
            $isGuest = $user->is_guest;
            $token = $user->generateApiToken($request->token_name, $isGuest);

            return response()->json([
                'ok' => true,
                'message' => 'New API token generated',
                'api_token' => $token,
                'token_type' => 'Bearer',
                'token_name' => $request->token_name ?? 'default',
                'expires_at' => $user->token_expires_at,
                'expires_in_seconds' => $user->getTokenRemainingSeconds(),
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to generate token',
                'error' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Revoke current API token
     * POST /api/auth/token/revoke
     * Requires: api_token middleware
     */
    public function revokeToken(Request $request): JsonResponse
    {
        $user = $request->user();

        if (!$user) {
            return response()->json([
                'ok' => false,
                'message' => 'Unauthorized',
            ], 401);
        }

        try {
            $user->update([
                'api_token' => null,
                'api_token_name' => null,
            ]);

            return response()->json([
                'ok' => true,
                'message' => 'API token revoked successfully',
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to revoke token',
                'error' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Validate API token
     * POST /api/auth/token/validate
     * Requires: api_token middleware
     */
    public function validateToken(Request $request): JsonResponse
    {
        $user = $request->user();

        if (!$user) {
            return response()->json([
                'ok' => false,
                'message' => 'Invalid token',
            ], 401);
        }

        return response()->json([
            'ok' => true,
            'message' => 'Token is valid',
            'user_id' => $user->id,
            'user_name' => $user->name,
        ]);
    }

    /**
     * Logout (revoke token)
     * POST /api/auth/logout
     * Requires: api_token middleware
     */
    public function logout(Request $request): JsonResponse
    {
        return $this->revokeToken($request);
    }

    /**
     * Update user profile
     * PUT /api/auth/profile
     * Requires: api_token middleware
     */
    public function updateProfile(Request $request): JsonResponse
    {
        $request->validate([
            'name' => 'nullable|string|max:255',
            'email' => 'nullable|email|unique:users,email,' . $request->user()->id,
            'current_password' => 'nullable|string',
            'password' => 'nullable|string|min:8|confirmed',
        ]);

        $user = $request->user();

        if (!$user) {
            return response()->json([
                'ok' => false,
                'message' => 'Unauthorized',
            ], 401);
        }

        try {
            // If changing password, validate current password
            if ($request->has('password')) {
                if (!$request->has('current_password')) {
                    return response()->json([
                        'ok' => false,
                        'message' => 'Current password required to change password',
                    ], 422);
                }

                if (!Hash::check($request->current_password, $user->password)) {
                    return response()->json([
                        'ok' => false,
                        'message' => 'Current password is incorrect',
                    ], 422);
                }

                $user->password = Hash::make($request->password);
            }

            if ($request->has('name')) {
                $user->name = $request->name;
            }

            if ($request->has('email')) {
                $user->email = $request->email;
            }

            $user->save();

            return response()->json([
                'ok' => true,
                'message' => 'Profile updated successfully',
                'user' => [
                    'id' => $user->id,
                    'name' => $user->name,
                    'email' => $user->email,
                ]
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to update profile',
                'error' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Helper: Generate API token for user
     */
    private function generateApiToken(User $user, ?string $tokenName = null): string
    {
        // Generate random token
        $plainToken = Str::random(80);

        // Hash and store in database
        $user->update([
            'api_token' => hash('sha256', $plainToken),
            'api_token_name' => $tokenName ?? 'default',
        ]);

        // Return unhashed token for user to store
        return $plainToken;
    }
