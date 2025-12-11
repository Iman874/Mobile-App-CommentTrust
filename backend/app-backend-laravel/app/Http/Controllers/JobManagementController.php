<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Artisan;

class JobManagementController extends Controller
{
    /**
     * Show job management page
     */
    public function index()
    {
        // Get job stats
        $pendingJobs = DB::table('jobs')->count();
        $runningJobs = 0; // Laravel doesn't track running jobs easily
        $failedJobs = DB::table('failed_jobs')->count();
        $completedJobs = DB::table('jobs')
            ->whereDate('created_at', today())
            ->count();

        // Get pending jobs list
        $pendingJobsList = DB::table('jobs')
            ->orderBy('created_at', 'desc')
            ->limit(50)
            ->get()
            ->map(function ($job) {
                $payload = json_decode($job->payload, true);
                return [
                    'id' => $job->id,
                    'type' => $payload['displayName'] ?? 'Unknown',
                    'queue' => $job->queue,
                    'created_at' => \Carbon\Carbon::createFromTimestamp($job->available_at),
                ];
            });

        // Get failed jobs list
        $failedJobsList = DB::table('failed_jobs')
            ->orderBy('failed_at', 'desc')
            ->limit(50)
            ->get()
            ->map(function ($job) {
                $payload = json_decode($job->payload, true);
                return [
                    'id' => $job->id,
                    'uuid' => $job->uuid,
                    'type' => $payload['displayName'] ?? 'Unknown',
                    'queue' => $job->queue,
                    'error' => $job->exception,
                    'failed_at' => \Carbon\Carbon::parse($job->failed_at),
                ];
            });

        return view('admin.jobs.index', compact(
            'pendingJobs',
            'runningJobs',
            'failedJobs',
            'completedJobs',
            'pendingJobsList',
            'failedJobsList'
        ));
    }

    /**
     * List jobs (API)
     */
    public function list()
    {
        $pendingJobs = DB::table('jobs')
            ->orderBy('created_at', 'desc')
            ->limit(100)
            ->get();

        $failedJobs = DB::table('failed_jobs')
            ->orderBy('failed_at', 'desc')
            ->limit(100)
            ->get();

        return response()->json([
            'ok' => true,
            'pending' => $pendingJobs,
            'failed' => $failedJobs,
            'stats' => [
                'pending_count' => DB::table('jobs')->count(),
                'failed_count' => DB::table('failed_jobs')->count(),
            ]
        ]);
    }

    /**
     * Retry a failed job (API)
     */
    public function retryJob($id)
    {
        try {
            // Retry using Artisan command
            Artisan::call('queue:retry', ['id' => $id]);

            return response()->json([
                'ok' => true,
                'message' => 'Job queued for retry'
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to retry job: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Cancel a pending job (API)
     */
    public function cancelJob($id)
    {
        try {
            $deleted = DB::table('jobs')->where('id', $id)->delete();

            if ($deleted) {
                return response()->json([
                    'ok' => true,
                    'message' => 'Job cancelled successfully'
                ]);
            }

            return response()->json([
                'ok' => false,
                'message' => 'Job not found'
            ], 404);
        } catch (\Exception $e) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to cancel job: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Delete a failed job (API)
     */
    public function deleteJob($id)
    {
        try {
            $deleted = DB::table('failed_jobs')->where('id', $id)->delete();

            if ($deleted) {
                return response()->json([
                    'ok' => true,
                    'message' => 'Failed job deleted successfully'
                ]);
            }

            return response()->json([
                'ok' => false,
                'message' => 'Failed job not found'
            ], 404);
        } catch (\Exception $e) {
            return response()->json([
                'ok' => false,
                'message' => 'Failed to delete job: ' . $e->getMessage()
            ], 500);
        }
    }
}
