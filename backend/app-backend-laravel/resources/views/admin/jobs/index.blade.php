@extends('admin.layout')

@section('page-title', 'Job Management')
@section('page-subtitle', 'Monitor and manage background jobs')

@section('admin-content')
<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
    <!-- Pending Jobs -->
    <div class="bg-white rounded-lg shadow p-6">
        <p class="text-gray-500 text-sm">Pending Jobs</p>
        <p class="text-3xl font-bold text-yellow-600">{{ $pendingJobs }}</p>
    </div>

    <!-- Running Jobs -->
    <div class="bg-white rounded-lg shadow p-6">
        <p class="text-gray-500 text-sm">Running Jobs</p>
        <p class="text-3xl font-bold text-blue-600">{{ $runningJobs }}</p>
    </div>

    <!-- Failed Jobs -->
    <div class="bg-white rounded-lg shadow p-6">
        <p class="text-gray-500 text-sm">Failed Jobs</p>
        <p class="text-3xl font-bold text-red-600">{{ $failedJobs }}</p>
    </div>

    <!-- Completed Jobs -->
    <div class="bg-white rounded-lg shadow p-6">
        <p class="text-gray-500 text-sm">Completed Today</p>
        <p class="text-3xl font-bold text-green-600">{{ $completedJobs }}</p>
    </div>
</div>

<!-- Job Queue Tabs -->
<div class="bg-white rounded-lg shadow">
    <div class="border-b border-gray-200">
        <div class="flex">
            <button onclick="switchTab('pending')" class="tab-btn active px-6 py-4 font-medium text-indigo-600 border-b-2 border-indigo-600">
                Pending
            </button>
            <button onclick="switchTab('failed')" class="tab-btn px-6 py-4 font-medium text-gray-600">
                Failed
            </button>
        </div>
    </div>

    <!-- Pending Jobs Tab -->
    <div id="pending-tab" class="tab-content p-6">
        <div class="overflow-x-auto">
            <table class="w-full">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Job ID</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Job Type</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Queue</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Created</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                    @forelse ($pendingJobsList as $job)
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-4 text-sm text-gray-900">{{ $job->id }}</td>
                            <td class="px-6 py-4 text-sm">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                    {{ explode('\\', $job->payload)[count(explode('\\', $job->payload))-1] ?? 'Unknown' }}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-600">{{ $job->queue }}</td>
                            <td class="px-6 py-4 text-sm text-gray-500">{{ $job->created_at->diffForHumans() }}</td>
                            <td class="px-6 py-4 text-sm space-x-2">
                                <button onclick="retryJob({{ $job->id }})" class="text-indigo-600 hover:text-indigo-900">Retry</button>
                                <button onclick="cancelJob({{ $job->id }})" class="text-red-600 hover:text-red-900">Cancel</button>
                            </td>
                        </tr>
                    @empty
                        <tr>
                            <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                                No pending jobs
                            </td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </div>

    <!-- Failed Jobs Tab -->
    <div id="failed-tab" class="tab-content hidden p-6">
        <div class="overflow-x-auto">
            <table class="w-full">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Job ID</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Job Type</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Error</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Failed At</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                    @forelse ($failedJobsList as $job)
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-4 text-sm text-gray-900">{{ $job->id }}</td>
                            <td class="px-6 py-4 text-sm">
                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                    {{ explode('\\', json_decode($job->payload, true)['displayName'] ?? 'Unknown')[0] ?? 'Unknown' }}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-600">
                                <button onclick="showError('{{ addslashes($job->exception) }}')" class="text-red-600 hover:text-red-900 underline">Show</button>
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-500">{{ $job->failed_at->diffForHumans() }}</td>
                            <td class="px-6 py-4 text-sm space-x-2">
                                <button onclick="retryJob({{ $job->id }})" class="text-indigo-600 hover:text-indigo-900">Retry</button>
                                <button onclick="deleteJob({{ $job->id }})" class="text-red-600 hover:text-red-900">Delete</button>
                            </td>
                        </tr>
                    @empty
                        <tr>
                            <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                                No failed jobs
                            </td>
                        </tr>
                    @endforelse
                </tbody>
            </table>
        </div>
    </div>
</div>

<script>
function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('border-b-2', 'border-indigo-600', 'text-indigo-600');
        btn.classList.add('text-gray-600');
    });

    document.getElementById(tabName + '-tab').classList.remove('hidden');
    event.target.classList.add('border-b-2', 'border-indigo-600', 'text-indigo-600');
    event.target.classList.remove('text-gray-600');
}

function retryJob(jobId) {
    if (confirm('Retry this job?')) {
        fetch(`/api/admin/jobs/${jobId}/retry`, {
            method: 'POST',
            headers: {
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
            }
        })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                alert('Job queued for retry');
                location.reload();
            }
        });
    }
}

function cancelJob(jobId) {
    if (confirm('Cancel this job?')) {
        fetch(`/api/admin/jobs/${jobId}/cancel`, {
            method: 'DELETE',
            headers: {
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
            }
        })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                alert('Job cancelled');
                location.reload();
            }
        });
    }
}

function deleteJob(jobId) {
    if (confirm('Delete this failed job?')) {
        fetch(`/api/admin/jobs/${jobId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content,
            }
        })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                alert('Job deleted');
                location.reload();
            }
        });
    }
}

function showError(error) {
    alert('Error:\n\n' + error);
}
</script>
@endsection
