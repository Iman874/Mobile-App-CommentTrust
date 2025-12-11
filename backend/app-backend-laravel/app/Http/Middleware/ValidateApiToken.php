<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;
use App\Models\User;

class ValidateApiToken
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        $token = $request->bearerToken();

        if (!$token) {
            return response()->json([
                'ok' => false,
                'message' => 'Missing API token',
                'error' => 'Unauthorized'
            ], 401);
        }

        // Hash the token to match what's stored in database
        $hashedToken = hash('sha256', $token);

        $user = User::where('api_token', $hashedToken)
            ->where('is_active', true)
            ->first();

        if (!$user) {
            return response()->json([
                'ok' => false,
                'message' => 'Invalid or inactive API token',
                'error' => 'Unauthorized'
            ], 401);
        }

        // Check if token has expired (for guest users)
        if ($user->isTokenExpired()) {
            return response()->json([
                'ok' => false,
                'message' => 'Your session has expired',
                'error' => 'token_expired',
                'is_guest' => $user->is_guest,
                'refresh_url' => $user->is_guest ? '/api/guest/refresh-token' : null,
            ], 401);
        }

        // Record API usage
        $user->recordApiUsage();

        // Attach user to request for use in controllers
        $request->setUserResolver(fn() => $user);

        return $next($request);
    }
}
