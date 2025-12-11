<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class CheckTokenExpiration
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        $user = $request->user();
        
        // If user is authenticated
        if ($user) {
            // Check if token has expired
            if ($user->isTokenExpired()) {
                // Log out the user by removing the token
                $user->update([
                    'api_token' => null,
                    'api_token_name' => null,
                ]);
                
                return response()->json([
                    'ok' => false,
                    'message' => 'Your session has expired',
                    'error' => 'token_expired',
                    'is_guest' => $user->is_guest,
                    'refresh_url' => $user->is_guest ? '/api/guest/refresh-token' : null,
                ], 401);
            }
        }
        
        return $next($request);
    }
}
